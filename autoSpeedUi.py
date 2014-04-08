import autoSpeed
import web
        
urls = (
    '/(.*)', 'mainController'
)
#app = web.application(urls, globals())

class mainController:        
    def GET(self, name):
        ping = autoSpeed.measurePing()
        bandwidth = autoSpeed.getThroughput()
        speedCap = autoSpeed.getRealSpeedCap()
        return "<h1>autoSpeed stats</h1><table>" + \
            "<tr><td>Ping</td><td>"+str(ping)+"</td></tr>"+ \
            "<tr><td>Bandwidth</td><td>"+str(bandwidth)+"</td></tr>"+ \
            "<tr><td>SpeedCap</td><td>"+str(speedCap)+"</td></tr>"+ \
            "</table>"

class MyApplication(web.application):
    def run(self, port=8080, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

if __name__ == "__main__":
    app = MyApplication(urls, globals())
    app.run(port=8888)
