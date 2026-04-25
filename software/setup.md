Complete instructions for settup up a fresh Raspberry Pi Zero 2 W to run notetaker software, raspberry pi os, and
setup other components.

## Flash SD Card

Download and Install Raspberry Pi Imager.
Settings:
- Device: Raspberry Pi Zero 2 W
- Os: Raspberry Pi OS (64-bit)
- Storage: 32gb microSD card

Before writing, click "Edit Settings" and configure:

```
Hostname: notebook
Username: pi
Password: (your password)
WiFi SSID: (your network name)
WiFi Password: (your password)
Country: US
SSH: enabled, password authentification
```
Click Save + Write.

## First Boot

Insert SD card into Pi. Power on. Wait about 90 seconds before attempting to connect

## SSH In
run the following commands in your Mac terminal:
```
ssh pi@notebook.local
```

If that fails, find the IP address:
```
ping notebook.local
ssh pi@<IP address>
```
If you get a host key error:
```
ssh-keygen -R notebook.local
ssh pi@notebook.local
```
## Enabling SPI and I2C
Onced SSH'ed into your pi terminal, enter the configuration menu
```
sudo raspi-config
```
Navigate to interface options and enable SPI and I2C.
Select finish, reboot with sudo reboot and SSH back in after 45 seconds.

## Install System Libraries
Libraries for python and using keyboard with i2c.
```
sudo apt update
sudo apt install -y python3-pip python3-pil python3-numpy python3-smbus i2c-tools git
```

## Install Waveshare Library
This is essential for the e-ink display to work correctly.
```
cd ~
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python
sudo pip3 install . --break-system-packages
```

## Verifying Hardware
```
sudo i2cdetect -y 1
```
With PiSugar S i2c disabled (cover up pins 3 + 5 with tape before connecting to Pi), you should see 5f somewhere on the table.

Test the display:
```
cd ~/e-Paper/RaspberryPi_JetsonNano/python/examples
python3 epd_2in13_V4_test.py
```
This will make the display show the Waveshare demo patterns from the library we installed earlier.

## Install the app
```
mkdir -p ~/notetaker
cd ~/notetaker
```
Copy 'app.py' from this repo to '/home/pi/notetaker/app.py' on the Pi
```
cat > ~/notetaker/app.py << 'EOF'
(paste your code here)
EOF
```
Test it manually:
```
python3 ~/notetaker/app.py
```

## Enable Autostart
Enabling autostart allows the program to be started upon booting up the device.
```
sudo bash -c 'cat > /etc/systemd/system/notetaker.service << EOF
[Unit]
Description=Notetaker App
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/notetaker/app.py
WorkingDirectory=/home/pi/notetaker
User=pi
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl enable notetaker
sudo systemctl start notetaker
```
Reboot and the app launches automatically, no need to SSH back in to start the app: 
Reboot and the app launches automatically:
```
sudo reboot
```
