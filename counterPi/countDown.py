import counter
import time

c = counter.Counter()
c.setup(4,5,6)
seconds=300

def countDown(seconds):
	#seconds is multiplied by 2, so we can blink the dots
	#seconds/60= minutes, /120 because we *2
	#minutes*100 to display in XX:00
	#seconds %60 for remaining seconds on this minute. display in 00:XX
	for i in range(seconds*2,-1,-1):
		c.display_number(int(int(i/120)*100+(i/2)%60),i%2)
		time.sleep(0.5)

countDown(seconds)

