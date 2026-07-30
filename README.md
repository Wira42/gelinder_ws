# gelinder_ws

Workspace ROS 2 (Humble) untuk robot **Gelinder** — *reconfigurable
rolling-crawling robot* dengan 4 lengan (A, B, C, D), masing-masing 3 sendi
serial (`continuous` joint, tanpa limit — cocok untuk mode roda/roller saat
robot berubah dari mode jalan ke mode rolling).

Target environment: **ROS 2 Humble + Gazebo Fortress (gz-sim / ros_gz)**.

## Apa yang diperbaiki dari file aslinya

File asli (`gelinder_ws.zip`) adalah hasil generate Fusion2urdf untuk
**ROS 1 Noetic** (`gelinder_urdf.zip` di root, lihat isi
`extras/other_sim_formats/` untuk file non-ROS lain seperti `.proto`
Webots dan `.usd` Isaac Sim) yang sebagian sudah diedit manual ke arah
`ament_cmake` tapi belum tuntas. Masalah yang ditemukan & diperbaiki:

1. **Struktur workspace salah** — ada `CMakeLists.txt`/`package.xml` nyasar
   di root `gelinder_ws/` (root workspace tidak boleh punya package sendiri).
   → dihapus; hanya `src/gelinder_description/` yang jadi package.
2. **`package.xml` campur ROS1/ROS2** — `format="2"` dengan depend `rospy`,
   padahal `CMakeLists.txt` sudah `ament_cmake`.
   → ditulis ulang ke `format="3"` murni ROS 2 dengan dependency yang
   relevan (`robot_state_publisher`, `ros2_control`, `gz_ros2_control`,
   `ros_gz_sim`, dst).
3. **Nama package tidak konsisten** — URDF memakai `Gelinder_description`
   (huruf besar) sementara folder paketnya `gelinder_description`, jadi
   semua `package://` dan `$(find ...)` gagal resolve.
   → disamakan jadi `gelinder_description` di semua tempat.
4. **Launch file masih XML ROS 1** (`.launch`) memakai `roslaunch`,
   `gazebo_ros`, `controller_manager/spawner` ala ROS1.
   → ditulis ulang sebagai `.launch.py` (Python launch ROS 2):
   `display.launch.py`, `gazebo.launch.py`, `controller.launch.py`.
5. **Plugin Gazebo Classic** (`libgazebo_ros_control.so`,
   `<mu1>`/`<mu2>` flat, `<material>Gazebo/Silver</material>`) — semua itu
   sintaks Gazebo Classic, tidak dikenali Gazebo Fortress (gz-sim).
   → diganti plugin `gz_ros2_control::GazeboSimROS2ControlPlugin`, friction
   lewat `<surface><friction><ode><mu>/<mu2></ode></friction></surface>`,
   dan warna tidak diatur ulang di gazebo.xacro (sudah dari `<material>`
   URDF aslinya).
6. **Tidak ada tag `<ros2_control>`** — wajib supaya `gz_ros2_control` tahu
   command/state interface tiap sendi.
   → ditambahkan `urdf/gelinder.ros2_control.xacro`, 12 joint dengan
   command_interface `position` + state_interface `position`/`velocity`.
7. **`controller.yaml` gaya ROS1** (`effort_controllers/JointPositionController`
   + `controller_manager/spawner` namespace `Gelinder`).
   → diganti `config/gelinder_controllers.yaml` gaya `ros2_control`:
   `joint_state_broadcaster`, `joint_trajectory_controller/JointTrajectoryController`
   (`gelinder_arm_controller`), dan `position_controllers/JointGroupPositionController`
   (`gelinder_position_controller`, nonaktif default, untuk uji manual cepat).
8. **`Gelinder.trans`** (transmission ROS1 `SimpleTransmission`, deprecated)
   → dihapus, fungsinya digantikan oleh tag `<ros2_control>`.
9. **`urdf.rviz`** adalah config **RViz 1** (`rviz/Displays` dst, tidak
   dikenal `rviz2`).
   → ditulis ulang jadi `rviz/gelinder.rviz` dengan kelas
   `rviz_default_plugins/...` (RViz 2).
10. File non-ROS (`Gelinder.proto` untuk Webots, folder `Gelinder/*.usd`
    untuk NVIDIA Isaac Sim) dipindah ke `extras/other_sim_formats/` agar
    tidak ikut ter-install sebagai bagian dari package ROS 2.
11. Line ending CRLF → LF pada semua file xacro/urdf.
12. Material `silver` tadinya hanya didefinisikan di dalam `xacro:macro`
    yang tidak pernah dipanggil, sehingga hasil expand URDF tidak punya
    definisi warna sama sekali. → didefinisikan langsung sebagai
    `<material name="silver">` top-level di `materials.xacro`.

Semua xacro sudah divalidasi expand secara independen (lihat bagian
verifikasi di bawah) dan menghasilkan pohon kinematik yang valid: 1 root
link (`base_link`), 13 link, 12 joint `continuous`, tanpa link yatim/putus.

## Struktur

```
gelinder_ws/
├── extras/other_sim_formats/      # file non-ROS (Webots .proto, Isaac Sim .usd) - referensi saja
└── src/gelinder_description/
    ├── CMakeLists.txt
    ├── package.xml
    ├── config/
    │   └── gelinder_controllers.yaml   # ros2_control controller manager config
    ├── launch/
    │   ├── display.launch.py           # RViz saja, tanpa Gazebo
    │   ├── gazebo.launch.py             # Gazebo Fortress + ros2_control
    │   └── controller.launch.py         # (re)spawn controller saja
    ├── meshes/*.stl
    ├── rviz/gelinder.rviz
    └── urdf/
        ├── gelinder.urdf.xacro          # file utama, include 3 file di bawah
        ├── gelinder.gazebo.xacro        # plugin gz_ros2_control + friction
        ├── gelinder.ros2_control.xacro  # <ros2_control> tag, 12 joint
        └── materials.xacro
```

## Cara build

Di komputer yang sudah ada ROS 2 Humble + Gazebo Fortress + paket berikut:

```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers \
                 ros-humble-gz-ros2-control ros-humble-ros-gz \
                 ros-humble-joint-state-publisher-gui ros-humble-xacro
```

Build:

```bash
cd gelinder_ws
colcon build --symlink-install
source install/setup.bash
```

## Cara test

**1. Cek URDF valid & RViz saja (tanpa Gazebo, paling cepat untuk debug model):**
```bash
ros2 launch gelinder_description display.launch.py
```
Harus muncul RViz dengan model Gelinder, dan slider joint_state_publisher_gui
untuk menggerakkan ke-12 sendi (A0..D2) secara manual.

**2. Simulasi penuh di Gazebo Fortress + ros2_control:**
```bash
ros2 launch gelinder_description gazebo.launch.py
```
Tunggu beberapa detik sampai `joint_state_broadcaster` dan
`gelinder_arm_controller` selesai di-spawn (lihat log terminal). Cek dengan:
```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
```

**3. Uji gerak manual lewat topic (tanpa trajectory controller):**
Aktifkan dulu `gelinder_position_controller` (nonaktif by default karena
bertabrakan dengan `gelinder_arm_controller` pada interface yang sama):
```bash
ros2 control switch_controllers --deactivate gelinder_arm_controller \
                                 --activate gelinder_position_controller
ros2 topic pub /gelinder_position_controller/commands std_msgs/msg/Float64MultiArray \
  "{data: [0,0,0, 0,0,0, 0,0,0, 0,0,0]}"
```

## Catatan untuk pengembangan algoritma transformasi jalan↔rolling

- Semua 12 sendi (`A0,A1,A2,B0,B1,B2,C0,C1,C2,D0,D1,D2`) bertipe
  `continuous` (tanpa limit sudut) — sudah sesuai untuk mode rolling
  (sendi roda berputar penuh).
- `gelinder_arm_controller` (`JointTrajectoryController`) adalah titik
  masuk yang disarankan untuk node algoritma transformasi: kirim
  `trajectory_msgs/JointTrajectory` dengan urutan waypoint untuk transisi
  mulus dari konfigurasi jalan (gait) ke konfigurasi rolling.
- File ini belum berisi logika gait/transformasi apa pun — itu akan jadi
  node terpisah (Python/C++) yang publish ke action
  `/gelinder_arm_controller/follow_joint_trajectory`.
