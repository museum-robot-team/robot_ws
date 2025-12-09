import os
from setuptools import setup

from glob import glob

package_name = 'servo_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Thêm dòng này để include launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kaiser',
    maintainer_email='longnguyen.31231025157@st.ueh.edu.vn',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
entry_points={
    'console_scripts': [
        'multi_servo_node = servo_control.multi_servo_node:main',
        'camera_tracker = servo_control.camera_tracker:main',
        'arm_animation = servo_control.arm_animation:main',
    ],
},
)
