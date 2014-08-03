# automatic speed limiter for variable bandwith connection

collection of small scripts i use on my OpenWrt router for dynamically shaping bandwidth via wshaper to use my variable speed connection ideally without running into timeout issues.

The problem is that my 3g internet sometimes gives me 6MBit but sometimes only 1MBit

What makes it even worse is that when it is slow and i start a download, my ping rates quickly rise from about 300ms to over 1.2 seconds! You can imagine that the internet connection isn't usable anymore at that point.

The only solution I found so far is to set a hard limit on the bandwidth in these cases to a value which will bring the ping times down to a reasonable level (<500ms).

The issue is that it cannot statically be determined what this ideal limit is because it changes over time.

The python script (autoSpeed.py) measures ping times and current throughput on a given network interface (ifconfig output) and determines if it is necessary to decrease the maximum bandwidth.

If the ping times are good and there is some significant traffic going on, it will also try to increase the speed limit again to provide good utilization of the available bandwidth.

## What's included

	autoSpeed.init
		init script for OpenWrt, do this to use it:
		cp autoSpeed.init /etc/init.d/autoSpeed; chmod ugo+x /etc/init.d/autoSpeed
		# activate it
		/etc/init.d/autoSpeed enable

	auto
		wrapper start script that runs the python script and pipes its output to logger so you can see it via "logread"

	speedCap
		a small wrapper script for getting/setting the speedCap for wshaper

	inetSpeed
		not really required, or an actual part of speedCap, just a command i often used for looking at the current throughput


## Dependencies:

* Python (2.7)
* Wshaper


by Paul Klingelhuber, 2014
