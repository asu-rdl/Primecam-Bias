import hardware; 
    
c = hardware.biascard(1); c.init_currsense(1); c.enable_all_chan()
import time 

with open("wbsc_characterization.csv", 'w') as filehandle:
    filehandle.write("wiper,bus,shunt,current\n")
    for iter in range(0, 1024):
        c.set_wiper(1, iter)
        time.sleep(0.25)
        b = c.get_bus(1)
        s = c.get_shunt(1)
        i = c.get_current(1)
        filehandle.write(f"{iter},{b:.4f},{s:.4f},{i:.4f}\n")
        print(f"{iter},{b:.4f},{s:.4f},{i:.4f}")

c.set_wiper(1, 0)
