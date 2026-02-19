const express = require('express');
const { getDatabase } = require('../database');

const router = express.Router();

/**
 * POST /api/users/register
 * 用户注册
 */
router.post('/register', (req, res) => {
  const db = getDatabase();
  const { username, password, nickname, phone } = req.body;

  if (!username || !password) {
    return res.status(400).json({ success: false, message: '用户名和密码不能为空' });
  }

  // 检查用户名是否已存在
  const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
  if (existing) {
    return res.status(409).json({ success: false, message: '用户名已存在' });
  }

  const result = db.prepare(
    `INSERT INTO users (username, password, nickname, phone, membership, created_at)
     VALUES (?, ?, ?, ?, 'free', datetime('now'))`
  ).run(username, password, nickname || username, phone || null);

  res.json({
    success: true,
    data: {
      id: result.lastInsertRowid,
      username,
      nickname: nickname || username,
      membership: 'free',
    },
  });
});

/**
 * POST /api/users/login
 * 用户登录
 */
router.post('/login', (req, res) => {
  const db = getDatabase();
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ success: false, message: '用户名和密码不能为空' });
  }

  const user = db.prepare(
    'SELECT id, username, nickname, membership, phone, created_at FROM users WHERE username = ? AND password = ?'
  ).get(username, password);

  if (!user) {
    return res.status(401).json({ success: false, message: '用户名或密码错误' });
  }

  res.json({
    success: true,
    data: user,
  });
});

/**
 * GET /api/users/:id
 * 获取用户信息
 */
router.get('/:id', (req, res) => {
  const db = getDatabase();
  const { id } = req.params;

  const user = db.prepare(
    'SELECT id, username, nickname, membership, phone, created_at FROM users WHERE id = ?'
  ).get(id);

  if (!user) {
    return res.status(404).json({ success: false, message: '用户不存在' });
  }

  res.json({ success: true, data: user });
});

/**
 * PUT /api/users/:id
 * 更新用户信息
 */
router.put('/:id', (req, res) => {
  const db = getDatabase();
  const { id } = req.params;
  const { nickname, phone } = req.body;

  const result = db.prepare(
    'UPDATE users SET nickname = COALESCE(?, nickname), phone = COALESCE(?, phone) WHERE id = ?'
  ).run(nickname || null, phone || null, id);

  if (result.changes === 0) {
    return res.status(404).json({ success: false, message: '用户不存在' });
  }

  const user = db.prepare(
    'SELECT id, username, nickname, membership, phone, created_at FROM users WHERE id = ?'
  ).get(id);

  res.json({ success: true, data: user });
});

/**
 * PUT /api/users/:id/membership
 * 升级会员
 */
router.put('/:id/membership', (req, res) => {
  const db = getDatabase();
  const { id } = req.params;
  const { membership } = req.body;

  const validLevels = ['free', 'premium', 'vip'];
  if (!validLevels.includes(membership)) {
    return res.status(400).json({ success: false, message: '无效的会员等级' });
  }

  const result = db.prepare(
    'UPDATE users SET membership = ? WHERE id = ?'
  ).run(membership, id);

  if (result.changes === 0) {
    return res.status(404).json({ success: false, message: '用户不存在' });
  }

  res.json({ success: true, data: { id: parseInt(id), membership } });
});

module.exports = router;
