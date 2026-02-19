// PM2 进程管理配置
// 使用方法: pm2 start ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'health-news',
      script: 'server/index.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
    },
  ],
};
