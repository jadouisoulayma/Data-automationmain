module.exports = {
  apps: [{
    name: 'dataautomation',
    script: '/root/dataAutomation/start_prod.sh',
    interpreter: '/bin/bash',
    cwd: '/root/dataAutomation',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      PYTHONUNBUFFERED: '1'
    },
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    error_file: '/root/dataAutomation/logs/pm2-error.log',
    out_file: '/root/dataAutomation/logs/pm2-out.log',
    merge_logs: true
  }]
};
