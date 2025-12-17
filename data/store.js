const bcrypt = require("bcryptjs");

const users = {
  customer1: {
    passwordHash: bcrypt.hashSync("bank123", 10),
    account: {
      balance: 2000,
      interestRate: 0.05,
      lastWithdrawal: null,
      currency: "USD"
    }
  }
};

module.exports = { users };