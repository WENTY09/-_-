document.addEventListener('DOMContentLoaded', function() {
    let activityChart = null;
    
    // Function to update the stats
    function updateStats() {
        fetch('/dashboard/api/stats')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching stats:', data.error);
                    return;
                }
                
                // Update system stats
                const cpuBar = document.getElementById('cpu-usage');
                cpuBar.style.width = `${data.system.cpu}%`;
                cpuBar.textContent = `${data.system.cpu}%`;
                cpuBar.setAttribute('aria-valuenow', data.system.cpu);
                
                const memoryBar = document.getElementById('memory-usage');
                memoryBar.style.width = `${data.system.memory}%`;
                memoryBar.textContent = `${data.system.memory}%`;
                memoryBar.setAttribute('aria-valuenow', data.system.memory);
                
                const diskBar = document.getElementById('disk-usage');
                diskBar.style.width = `${data.system.disk}%`;
                diskBar.textContent = `${data.system.disk}%`;
                diskBar.setAttribute('aria-valuenow', data.system.disk);
                
                document.getElementById('system-uptime').textContent = data.system.uptime;
                
                // Update bot stats
                document.getElementById('stats-users-count').textContent = data.bot.total_users;
                document.getElementById('stats-deliveries-count').textContent = data.bot.total_deliveries;
                document.getElementById('stats-earnings-count').textContent = data.bot.total_earnings;
                document.getElementById('stats-buffs-count').textContent = data.bot.active_buffs;
                
                // Update chart data if available
                if (!activityChart) {
                    initChart();
                }
            })
            .catch(error => {
                console.error('Error fetching stats:', error);
            });
    }
    
    // Function to initialize the activity chart
    function initChart() {
        const ctx = document.getElementById('activity-chart').getContext('2d');
        
        // Create initial data (we'll add real data later)
        const labels = [];
        const now = new Date();
        
        // Create labels for the last 24 hours
        for (let i = 24; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.getHours() + ':00');
        }
        
        const data = {
            labels: labels,
            datasets: [
                {
                    label: 'Доставки',
                    data: Array(25).fill(0).map(() => Math.floor(Math.random() * 100)),
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    tension: 0.1
                },
                {
                    label: 'Активные пользователи',
                    data: Array(25).fill(0).map(() => Math.floor(Math.random() * 50)),
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }
            ]
        };
        
        const config = {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Активность за последние 24 часа'
                    }
                }
            }
        };
        
        activityChart = new Chart(ctx, config);
    }
    
    // Initial update
    updateStats();
    
    // Auto-refresh every 5 seconds
    setInterval(updateStats, 5000);
});
