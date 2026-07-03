import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'amr_explore'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Masimba',
    maintainer_email='Masimba249@gmail.com',
    description='Frontier-based autonomous exploration for the AMR',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'frontier_explorer = amr_explore.frontier_explorer:main',
        ],
    },
)
