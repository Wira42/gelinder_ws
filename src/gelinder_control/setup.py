from setuptools import find_packages, setup

package_name = "gelinder_control"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/transform_and_roll.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="syuntoku14",
    maintainer_email="syuntoku14@todo.todo",
    description=(
        "Locomotion mode nodes for the Gelinder reconfigurable "
        "rolling-crawling robot (transform_to_roll, roll_forward, "
        "roll_left, roll_right, roll_center)."
    ),
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "transform_to_roll = gelinder_control.transform_to_roll:main",
            "roll_forward = gelinder_control.roll_forward:main",
            "roll_left = gelinder_control.roll_left:main",
            "roll_right = gelinder_control.roll_right:main",
            "roll_center = gelinder_control.roll_center:main",
        ],
    },
)
