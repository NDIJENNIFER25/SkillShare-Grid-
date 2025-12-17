const request = require('supertest');
const app = require('../server');

describe('Account endpoints', () => {
  let token;

  beforeAll(async () => {
    const res = await request(app)
      .post('/auth/login')
      .send({ username: 'customer1', password: 'bank123' });
    token = res.body.token;
  });

  test('GET /api/account returns account data when authenticated', async () => {
    const res = await request(app)
      .get('/api/account')
      .set('Authorization', `Bearer ${token}`);
    expect(res.statusCode).toBe(200);
    expect(res.body).toHaveProperty('balance');
    expect(res.body).toHaveProperty('currency');
  });
});
