import math
import threading
import time
from collections import deque

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

FREE = 0
UNKNOWN = -1
MIN_FRONTIER_CELLS = 6
GOAL_DEDUPE_RADIUS = 0.4
GOAL_TIMEOUT_SEC = 30.0
# slam_toolbox's map_update_interval is 5s, so a map that looks fully
# explored on one check may just be stale -- wait through several update
# cycles before believing it.
ROUNDS_WITHOUT_FRONTIERS_BEFORE_STOP = 8
NO_FRONTIER_RETRY_DELAY_SEC = 3.0
MAX_ROUNDS = 200


class MapListener(Node):
    def __init__(self):
        super().__init__('frontier_explorer_map_listener')
        self.map_data = None
        qos = QoSProfile(depth=1)
        qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        qos.reliability = QoSReliabilityPolicy.RELIABLE
        self.create_subscription(OccupancyGrid, '/map', self._map_cb, qos)

    def _map_cb(self, msg):
        self.map_data = msg


def find_frontiers(grid: OccupancyGrid):
    w, h = grid.info.width, grid.info.height
    data = grid.data

    def idx(x, y):
        return y * w + x

    frontier_mask = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            i = row + x
            if data[i] != FREE:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and data[idx(nx, ny)] == UNKNOWN:
                    frontier_mask[i] = 1
                    break

    visited = bytearray(w * h)
    clusters = []
    for y in range(h):
        for x in range(w):
            i = idx(x, y)
            if not frontier_mask[i] or visited[i]:
                continue
            q = deque([(x, y)])
            visited[i] = 1
            cluster = []
            while q:
                cx, cy = q.popleft()
                cluster.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        ni = idx(nx, ny)
                        if frontier_mask[ni] and not visited[ni]:
                            visited[ni] = 1
                            q.append((nx, ny))
            if len(cluster) >= MIN_FRONTIER_CELLS:
                clusters.append(cluster)

    ox, oy = grid.info.origin.position.x, grid.info.origin.position.y
    res = grid.info.resolution
    frontiers = []
    for cluster in clusters:
        # The raw average of a cluster's cells is not necessarily itself a
        # frontier cell -- a full-circle scan produces a ring-shaped
        # cluster whose average sits back at the ring's center (i.e. on
        # top of the robot). Snap to the actual member cell nearest that
        # average instead, so the goal always lands on real frontier.
        avg_x = sum(p[0] for p in cluster) / len(cluster)
        avg_y = sum(p[1] for p in cluster) / len(cluster)
        gx, gy = min(cluster, key=lambda p: (p[0] - avg_x) ** 2 + (p[1] - avg_y) ** 2)
        wx = ox + (gx + 0.5) * res
        wy = oy + (gy + 0.5) * res
        frontiers.append((wx, wy, len(cluster)))
    return frontiers


def make_goal(clock, x, y):
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.header.stamp = clock.now().to_msg()
    goal.pose.position.x = x
    goal.pose.position.y = y
    goal.pose.orientation.w = 1.0
    return goal


def main():
    rclpy.init()
    map_listener = MapListener()
    navigator = BasicNavigator()
    # goToPose() waits for the NavigateToPose action server itself, so no
    # separate readiness wait is needed here. (waitUntilNav2Active() polls
    # each node's lifecycle GetState service instead, which is unnecessary
    # for our purposes and there's no amcl in this SLAM-mapping setup for
    # it to check anyway.)

    # map_listener gets its own multi-threaded executor spinning continuously
    # in the background. With use_sim_time on, every node also subscribes to
    # /clock internally, and that subscription is serviced ahead of ours in
    # a single-threaded spin_once loop -- since Gazebo publishes /clock
    # continuously, a single-threaded spin_once never gets around to our
    # one-shot /map callback. Multi-threading lets both be serviced.
    map_executor = MultiThreadedExecutor(num_threads=2)
    map_executor.add_node(map_listener)
    map_spin_thread = threading.Thread(target=map_executor.spin, daemon=True)
    map_spin_thread.start()

    attempted_goals = []  # every goal ever sent, kept for the full run
    rounds_without_frontiers = 0

    for round_num in range(MAX_ROUNDS):
        if map_listener.map_data is None:
            navigator.get_logger().info('Waiting for /map...')
            time.sleep(1.0)
            continue

        frontiers = find_frontiers(map_listener.map_data)
        frontiers.sort(key=lambda f: -f[2])

        target = None
        for wx, wy, _size in frontiers:
            if all(math.hypot(wx - vx, wy - vy) > GOAL_DEDUPE_RADIUS
                   for vx, vy in attempted_goals):
                target = (wx, wy)
                break

        if target is None:
            rounds_without_frontiers += 1
            navigator.get_logger().info(
                f'No reachable frontiers ({rounds_without_frontiers}/'
                f'{ROUNDS_WITHOUT_FRONTIERS_BEFORE_STOP})'
            )
            if rounds_without_frontiers >= ROUNDS_WITHOUT_FRONTIERS_BEFORE_STOP:
                navigator.get_logger().info('Exploration complete: map fully covered.')
                break
            time.sleep(NO_FRONTIER_RETRY_DELAY_SEC)
            continue

        rounds_without_frontiers = 0
        attempted_goals.append(target)
        navigator.get_logger().info(f'Heading to frontier ({target[0]:.2f}, {target[1]:.2f})')
        accepted = navigator.goToPose(make_goal(map_listener.get_clock(), *target))

        if not accepted:
            navigator.get_logger().info('Goal rejected, blacklisting and backing off.')
            time.sleep(1.0)
            continue

        start = time.time()
        while not navigator.isTaskComplete():
            time.sleep(0.5)
            if time.time() - start > GOAL_TIMEOUT_SEC:
                navigator.cancelTask()
                break

        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            navigator.get_logger().info('Reached frontier.')
        else:
            navigator.get_logger().info(f'Frontier goal ended with: {result}')

    # Deliberately NOT calling navigator.lifecycleShutdown() here: it tears
    # down the *entire shared* Nav2 lifecycle stack (controller_server,
    # planner_server, bt_navigator, ...) via lifecycle_manager_navigation.
    # That stack is owned by amr_navigation's own launch file, not by this
    # node -- this node is just a client of it.
    map_executor.shutdown()
    map_listener.destroy_node()
    navigator.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
