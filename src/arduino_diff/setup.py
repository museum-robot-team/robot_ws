from setuptools import setup

package_name = 'arduino_diff'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/diff_odom.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='YourName',
    maintainer_email='you@example.com',
    description='Node to compute odometry from Arduino ROSArduinoBridge protocol',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'diff_odom = arduino_diff.arduino_diff_node:main',
        ],
    },
)