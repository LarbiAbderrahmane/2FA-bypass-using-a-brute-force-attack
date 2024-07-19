from classes.CConsole import CConsole
from classes.Attacker import Attacker
import asyncio
import time


t0 = time.perf_counter()

with CConsole() as console:
    Attacker(console).start_attack()

print("time took", time.perf_counter()-t0)