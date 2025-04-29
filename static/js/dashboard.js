const tg = window.Telegram.WebApp;
tg.expand();

// Initialize Telegram WebApp
document.addEventListener('DOMContentLoaded', function() {
    if (tg.initDataUnsafe?.user?.id) {
        loadUserData(tg.initDataUnsafe.user.id);
    }
});

async function loadUserData(userId) {
    try {
        const response = await fetch(`/api/user/${userId}`);
        const data = await response.json();

        document.getElementById('deliveries').textContent = data.deliveries || 0;
        document.getElementById('balance').textContent = data.balance || 0;
        document.getElementById('rank').textContent = data.rank || '-';

        if (data.active_buffs) {
            updateBuffs(data.active_buffs);
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

function updateBuffs(buffs) {
    const buffsList = document.getElementById('buffs-list');
    buffsList.innerHTML = '';

    buffs.forEach(buff => {
        const buffItem = document.createElement('div');
        buffItem.className = 'buff-item';
        buffItem.innerHTML = `
            <div class="buff-content">
                <h4>${buff.name}</h4>
                <p>+${buff.bonus}% к доходу</p>
                <p>Осталось: ${buff.remaining_minutes} мин</p>
            </div>
        `;
        buffsList.appendChild(buffItem);
    });
}

// Button handlers
document.querySelector('.delivery-button').addEventListener('click', function() {
    tg.sendData(JSON.stringify({action: 'start_delivery'}));
});

document.querySelector('.shop-button').addEventListener('click', function() {
    tg.sendData(JSON.stringify({action: 'open_shop'}));
});

function updateLeaderboard() {
    fetch('/api/leaderboard')
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById('top-couriers');
            list.innerHTML = data.map((user, index) => `
                <div class="leaderboard-item">
                    <span class="position">${index + 1}</span>
                    <span class="name">${user.name}</span>
                    <span class="score">${user.deliveries} доставок</span>
                </div>
            `).join('');
        });
}


// Update stats every 30 seconds
setInterval(() => {
    if (tg.initDataUnsafe?.user?.id) {
        loadUserData(tg.initDataUnsafe.user.id);
    }
    updateLeaderboard();
}, 30000);