const http = require('http');

function postJson(path, data) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const opts = {
      hostname: 'localhost',
      port: process.env.PORT || 3000,
      path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = http.request(opts, (res) => {
      let out = '';
      res.setEncoding('utf8');
      res.on('data', (c) => (out += c));
      res.on('end', () => {
        try {
          resolve({ statusCode: res.statusCode, body: JSON.parse(out) });
        } catch (err) {
          resolve({ statusCode: res.statusCode, body: out });
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function getJson(path, token) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: 'localhost',
      port: process.env.PORT || 3000,
      path,
      method: 'GET',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    };

    const req = http.request(opts, (res) => {
      let out = '';
      res.setEncoding('utf8');
      res.on('data', (c) => (out += c));
      res.on('end', () => {
        try {
          resolve({ statusCode: res.statusCode, body: JSON.parse(out) });
        } catch (err) {
          resolve({ statusCode: res.statusCode, body: out });
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

(async () => {
  try {
    console.log('Testing: POST /auth/login');
    const login = await postJson('/auth/login', { username: 'customer1', password: 'bank123' });
    console.log('Login response:', login.statusCode, login.body);
    if (!login.body || !login.body.token) {
      console.error('Login failed — stopping tests.');
      process.exit(2);
    }

    const token = login.body.token;
    console.log('Testing: GET /api/account with token');
    const acct = await getJson('/api/account', token);
    console.log('Account response:', acct.statusCode, acct.body);

    process.exit(0);
  } catch (err) {
    console.error('Integration test failed:', err);
    process.exit(1);
  }
})();
