const request = require('supertest');
const app = require('../server');

describe('Auth endpoints', () => {
  test('POST /auth/login returns token for valid credentials', async () => {
    const res = await request(app)
      .post('/auth/login')
      .send({ username: 'customer1', password: 'bank123' })
      .set('Accept', 'application/json');
    expect(res.statusCode).toBe(200);
    expect(res.body).toHaveProperty('token');
    expect(typeof res.body.token).toBe('string');
  });

  test('POST /auth/login returns 401 for invalid password', async () => {
    const res = await request(app)
      .post('/auth/login')
      .send({ username: 'customer1', password: 'wrong' })
      .set('Accept', 'application/json');
    expect(res.statusCode).toBe(401);
  });
});
