import sys
from daemon import Daemon

class pantalaimon(Daemon):
    def run(self):
        # Do stuff

try:
    pineMarten = pantalaimon('/path/to/pid.pid')

    if(str.lower(str(sys.argv[1])) == "stop"):
	pineMarten.stop()        
        exit(1)

    if(str.lower(str(sys.argv[1])) == "start"):
        pineMarten.start()


    if(str.lower(str(sys.argv[1])) == "restart"):
        pineMarten.restart()
    
    if(str.lower(str(sys.argv[1])) == "debug"):
        pineMarten.run()
 
    else:
        print "The argument is missing. The authorized arguments are start , stop , restart , debug"
        pass

except Exception as e:
    print "The argument is missing. The authorized arguments are start , stop , restart , debug"
