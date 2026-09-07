# Drone video → ground station over Tailscale

Stream live video from a Raspberry Pi 5 + Camera Module 3 on a drone to a Windows
laptop anywhere with internet. No port forwarding, no static IP, no LAN required.

```
Pi 5 + Camera  ──►  Tailscale (WireGuard)  ──►  Windows laptop
   (drone)              over internet            (ffplay)
```

## Files

| File | Where it goes |
|---|---|
| `stream.sh` | Pi — starts the stream |
| `picam.service` | Pi — makes it start on boot |
| `view.bat` | Windows — opens the video window |

---

## Part 1 — Windows (5 minutes)

You already have Tailscale installed. Just get your laptop's Tailscale IP:

```powershell
tailscale ip -4
```

Write it down — something like `100.200.201.202`. This address is permanent and works
from any network.

Install a player:

```powershell
winget install --id Gyan.FFmpeg -e
```

Close and reopen PowerShell afterwards.

---

## Part 2 — Pi (10 minutes)

SSH into the Pi and run these.

**1. Install Tailscale**

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```

It prints a URL. Open it in a browser, sign in with **the same account as your laptop**.

**2. Stop the key from expiring**

In the Tailscale admin console → **Machines** → click your Pi → **"..."** menu →
**Disable key expiry**.

Skip this and the stream stops working in 180 days with no obvious cause.

**3. Check the camera**

```bash
rpicam-hello --list-cameras
```

You should see a line containing `imx708`. If not, power off and reseat the ribbon cable.

**4. Install the stream script**

```bash
git clone https://github.com/YOURNAME/YOURREPO.git
cd YOURREPO
chmod +x stream.sh
```

Open `stream.sh` and put your laptop's Tailscale IP in the first line:

```bash
nano stream.sh
```

**5. Start it on boot**

```bash
sudo cp picam.service /etc/systemd/system/
sudo nano /etc/systemd/system/picam.service     # set User= and the path to stream.sh
sudo systemctl daemon-reload
sudo systemctl enable --now picam
```

Check it's running:

```bash
systemctl status picam
```

---

## Flying

Power the drone. The Pi streams automatically once it has internet.

On the laptop, double-click **`view.bat`** (edit the port inside if you changed it).

Or from PowerShell:

```powershell
ffplay -fflags nobuffer -flags low_delay -framedrop "udp://@:5000"
```

You can close and reopen the viewer mid-flight. The Pi keeps pushing regardless.

---

## Settings

Everything is at the top of `stream.sh`:

| Setting | Default | Change it when |
|---|---|---|
| `LAPTOP_IP` | — | **Must be set.** Your laptop's Tailscale IP. |
| `WIDTH`/`HEIGHT` | 1280×720 | Drop to 854×480 if the link struggles |
| `FPS` | 25 | |
| `BITRATE` | 2000000 | Lower first if video breaks up |

After editing: `sudo systemctl restart picam`

---

## If it doesn't work

**Black window, no errors** — Windows Firewall. Allow ffplay on **both** Private and
Public profiles. This is the most common cause.

**Nothing arrives at all** — check the tunnel from Windows:

```powershell
tailscale status
tailscale ping <pi-hostname>
```

Both machines must show up. If the Pi is missing, it isn't signed in to the same account.

**Video breaks up or freezes** — your uplink is saturated. Lower `BITRATE` to `1200000`
and resolution to 854×480, then restart the service.

**Half-second lag** — expected. On a cellular connection you're almost certainly behind
carrier NAT, so Tailscale routes through a relay server instead of connecting directly.
Check with `tailscale ping <pi-hostname>`: if it says `via DERP`, that's your situation
and there's no fix from your side. It still works fine for monitoring.

**Camera not found** — reseat the ribbon at both ends. On a Pi 5 you need the
**22-pin-to-15-pin** cable, not the one that ships in the Camera Module 3 box.

**Check the logs**

```bash
journalctl -u picam -f
```

---

## Don't rely on the stream for your footage

A dropped link means lost video. Record onboard in parallel — SSH in and run:

```bash
rpicam-vid -t 0 -n --width 1920 --height 1080 -o ~/flight_$(date +%F_%H%M).mp4
```

The stream is for the operator. The SD card is your data.
