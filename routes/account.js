const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { users } = require('../data/store');

// All account routes require a valid JWT
router.use(auth);

function getAccountForReq(req) {
  const username = req.user && req.user.username;
  if (!username) return null;
  const user = users[username];
  return user && user.account ? user.account : null;
}

// GET account details
router.get('/', (req, res) => {
  const account = getAccountForReq(req);
  if (!account) return res.status(404).json({ message: 'Account not found' });
  res.json(account);
});

// POST withdraw
router.post('/withdraw', (req, res) => {
  const amount = Number(req.body.amount);
  if (Number.isNaN(amount)) return res.status(400).json({ message: 'Amount must be a number' });
  if (amount <= 0) return res.status(400).json({ message: 'Invalid withdrawal amount' });

  const account = getAccountForReq(req);
  if (!account) return res.status(404).json({ message: 'Account not found' });

  if (amount > account.balance) {
    return res.status(400).json({ message: 'Insufficient funds' });
  }

  account.balance -= amount;
  account.lastWithdrawal = amount;

  res.json({
    message: 'Withdrawal successful',
    balance: account.balance,
    lastWithdrawal: account.lastWithdrawal
  });
});

// GET interest
router.get('/interest', (req, res) => {
  const account = getAccountForReq(req);
  if (!account) return res.status(404).json({ message: 'Account not found' });

  const yearlyInterest = account.balance * account.interestRate;
  const monthlyInterest = yearlyInterest / 12;

  res.json({
    balance: account.balance,
    interestRate: account.interestRate,
    yearlyInterest,
    monthlyInterest,
    currency: account.currency
  });
});

module.exports = router;