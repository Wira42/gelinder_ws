# gelinder_control

Node-node mode locomotion untuk robot Gelinder, supaya tidak perlu lagi
manual `ros2 action send_goal` / `ros2 topic pub` setiap kali ingin
mengubah mode. Setiap mode adalah satu node yang dijalankan dengan
`ros2 run gelinder_control <nama_node>`.

## Mode yang tersedia

| Command | Fungsi |
|---|---|
| `ros2 run gelinder_control transform_to_roll` | Melipat ke-12 sendi ke 0 rad (bentuk roda), lalu node otomatis selesai/exit. |
| `ros2 run gelinder_control roll_forward` | Menggelindingkan badan lurus ke depan (semua roda kecepatan sama). |
| `ros2 run gelinder_control roll_center` | Sama seperti `roll_forward` (alias, sesuai istilah "tengah"). |
| `ros2 run gelinder_control roll_left` | Belok kiri sambil menggelinding (sisi kiri melambat). |
| `ros2 run gelinder_control roll_right` | Belok kanan sambil menggelinding (sisi kanan melambat). |

**Urutan pakai yang benar:** jalankan `transform_to_roll` dulu (sekali),
baru setelah itu salah satu dari `roll_forward`/`roll_left`/`roll_right`/`roll_center`.
Node rolling TIDAK mengubah bentuk robot — ia cuma memutar sendi yang
sudah dalam posisi roda.

```bash
ros2 run gelinder_control transform_to_roll
ros2 run gelinder_control roll_forward
# tekan Ctrl+C untuk berhenti
```

Atau sekaligus dalam satu command (transform lalu otomatis roll_forward):
```bash
ros2 launch gelinder_control transform_and_roll.launch.py
ros2 launch gelinder_control transform_and_roll.launch.py speed:=2.0 duration_sec:=5.0
```

## Parameter yang bisa diubah

Semua node rolling menerima parameter lewat `--ros-args -p nama:=nilai`:

```bash
# putar lebih cepat, otomatis stop setelah 4 detik
ros2 run gelinder_control roll_forward --ros-args -p speed:=2.0 -p duration_sec:=4.0

# belok kiri lebih tajam (turn_ratio kecil = belokan tajam, 0 = pivot di tempat)
ros2 run gelinder_control roll_left --ros-args -p speed:=1.0 -p turn_ratio:=0.15
```

| Parameter | Node | Default | Arti |
|---|---|---|---|
| `speed` | semua roll_* | 1.0 | Kecepatan putar roda (rad/s). Negatif = mundur. |
| `duration_sec` | semua roll_*, transform_to_roll | 0.0 (roll_*) / 3.0 (transform) | Lama bergerak (detik). 0 di node roll_* = jalan terus sampai Ctrl+C. |
| `turn_ratio` | roll_left, roll_right | 0.4 | Skala kecepatan sisi dalam tikungan (0=pivot di tempat, 1=lurus, sama dengan roll_forward). |
| `rate_hz` | semua roll_* | 20.0 | Frekuensi publish ulang command kecepatan. |

## Cara kerja (arsitektur)

Robot punya 2 command interface per sendi: `position` dan `velocity`
(lihat `urdf/gelinder.ros2_control.xacro` di package `gelinder_description`).
ros2_control hanya mengizinkan **satu controller aktif** per command
interface, jadi setiap node mode otomatis melakukan **switch controller**
lewat service `/controller_manager/switch_controller` sebelum bergerak:

- `transform_to_roll` → mengaktifkan `gelinder_arm_controller`
  (position-based, `JointTrajectoryController`) untuk gerak ke posisi 0
  yang presisi dan mulus.
- `roll_forward` / `roll_left` / `roll_right` / `roll_center` →
  mengaktifkan `gelinder_velocity_controller` (velocity-based,
  `JointGroupVelocityController`) untuk putaran kontinyu seperti roda.

Logika switch-nya ada di `gelinder_control/controller_switch.py`, dipakai
bersama oleh semua node — jadi kalau mau ubah cara switching, cukup edit
satu file itu.

## Kalibrasi arah putaran (PENTING, lakukan ini dulu)

Ke-4 lengan (A, B, C, D) didefinisikan terpisah di file CAD asli
(Fusion2urdf), dan ternyata **axis rotasi-nya tidak seragam** — A0/D0
punya axis Z = −1, B0/C0 punya axis Z = +1. Artinya mengirim kecepatan
yang sama persis ke 12 sendi **belum pasti** membuat semua lengan
berputar ke arah fisik yang sama.

File `gelinder_control/rolling_config.py` punya dictionary `FORWARD_SIGN`
persis untuk menangani ini — defaultnya semua `+1.0`. Cara kalibrasi:

1. `ros2 run gelinder_control transform_to_roll`
2. `ros2 run gelinder_control roll_forward`
3. Amati robot di Gazebo:
   - Kalau menggelinding mulus ke satu arah → selesai, tidak perlu ubah apa-apa.
   - Kalau ada lengan yang "melawan" arah lengan lain (badan bergetar di
     tempat / tidak menggelinding bersih) → buka `rolling_config.py`,
     balik tanda lengan yang salah dari `+1.0` jadi `-1.0` (atau
     sebaliknya), simpan, `colcon build` lagi, ulangi tes.
4. Setelah `roll_forward` benar, `roll_left`/`roll_right`/`roll_center`
   otomatis ikut benar karena memakai `FORWARD_SIGN` yang sama.

Sisi kiri robot = lengan A (depan-kiri) + C (belakang-kiri).
Sisi kanan robot = lengan B (depan-kanan) + D (belakang-kanan).
(Lihat koordinat origin tiap joint di `gelinder.urdf.xacro` kalau perlu
verifikasi ulang.)

## Build & jalankan

```bash
cd ~/gelinder_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

ros2 launch gelinder_description gazebo.launch.py   # di terminal 1, tunggu sampai robot muncul

# di terminal 2 (baru):
source ~/gelinder_ws/install/setup.bash
ros2 run gelinder_control transform_to_roll
ros2 run gelinder_control roll_forward
```

## Troubleshooting

- **"Could not activate gelinder_arm_controller/gelinder_velocity_controller"**
  → pastikan `gazebo.launch.py` sudah jalan dan `ros2 control list_controllers`
  menunjukkan kedua controller itu ada (boleh salah satu `inactive`, itu normal).
- **Robot tidak bergerak sama sekali saat roll_forward**
  → cek `ros2 topic hz /gelinder_velocity_controller/commands` untuk
  pastikan node memang publish. Cek juga `ros2 control list_hardware_interfaces`
  untuk lihat apakah interface `velocity` sedang "claimed".
- **Robot bergerak tapi arahnya aneh/lengan saling melawan**
  → ikuti langkah kalibrasi `FORWARD_SIGN` di atas.
