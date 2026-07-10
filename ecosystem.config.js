const path = require('path');

const APP_ROOT = __dirname;

module.exports = {
  apps: [
    {
      name: 'data-sync-service',
      script: 'python3',
      args: 'main.py',
      cwd: APP_ROOT,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env_file: path.join(APP_ROOT, '.env'),
      env: {
        PYTHONPATH: path.join(APP_ROOT, 'src'),
      },
    },
  ],
};
