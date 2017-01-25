#!/usr/bin/env python

import mym

app = mym.create_app()
app.run(host='0.0.0.0',
        threaded=True,
        debug=True)
