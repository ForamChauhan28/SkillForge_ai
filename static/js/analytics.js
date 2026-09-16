document.addEventListener('DOMContentLoaded', () => {
    initProgressChart();
    initRadarChart();
    initCounters();
});

function initProgressChart() {
    const canvas = document.getElementById('progressChart');
    if (!canvas) return;

    const completed = parseFloat(canvas.getAttribute('data-completed')) || 0;
    const remaining = Math.max(0, 100 - completed);

    const ctx = canvas.getContext('2d');
    
    // Custom plugin to show percentage in the middle
    const centerTextPlugin = {
        id: 'centerText',
        beforeDraw: function(chart) {
            const width = chart.width, height = chart.height, ctx = chart.ctx;
            ctx.restore();
            const fontSize = (height / 114).toFixed(2);
            ctx.font = "bold " + fontSize + "em Inter, sans-serif";
            ctx.textBaseline = "middle";
            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-primary') || '#000';
            
            const text = Math.round(completed) + "%",
                textX = Math.round((width - ctx.measureText(text).width) / 2),
                textY = height / 2;
                
            ctx.fillText(text, textX, textY);
            ctx.save();
        }
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Remaining'],
            datasets: [{
                data: [completed, remaining],
                backgroundColor: [
                    '#4a3f8a', // accent purple
                    '#ede7db'  // light gray
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            }
        },
        plugins: [centerTextPlugin]
    });
}

function initRadarChart() {
    const canvas = document.getElementById('radarChart');
    const container = document.getElementById('radarChartContainer');
    const loading = document.getElementById('radarLoading');
    const errorMsg = document.getElementById('radarError');
    if (!canvas) return;

    fetch('/api/skill-gap')
        .then(res => res.json())
        .then(data => {
            loading.style.display = 'none';
            if (data.error || (!data.categories && !data.labels) || (data.categories && data.categories.length === 0)) {
                errorMsg.classList.remove('hidden');
                return;
            }
            
            container.style.display = 'block';
            
            const ctx = canvas.getContext('2d');
            // Map API response fields (categories/current_levels/required_levels) 
            // to chart fields (labels/datasets)
            const labels = data.categories || data.labels || [];
            const currentLevels = data.current_levels || data.user_skills || [];
            const requiredLevels = data.required_levels || data.required_skills || [];
            
            new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Your Skills',
                            data: currentLevels,
                            backgroundColor: 'rgba(74, 63, 138, 0.3)',
                            borderColor: '#4a3f8a',
                            pointBackgroundColor: '#4a3f8a',
                            borderWidth: 2
                        },
                        {
                            label: 'Required Level',
                            data: requiredLevels,
                            backgroundColor: 'rgba(201, 168, 76, 0.3)',
                            borderColor: '#c9a84c',
                            pointBackgroundColor: '#c9a84c',
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            min: 0,
                            max: 10,
                            ticks: {
                                stepSize: 2,
                                backdropColor: 'transparent'
                            }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error('Failed to load skill gap data', err);
            loading.style.display = 'none';
            errorMsg.classList.remove('hidden');
        });
}

function initCounters() {
    const counters = document.querySelectorAll('.counter');
    const speed = 200;

    counters.forEach(counter => {
        const target = +counter.getAttribute('data-target');
        if(isNaN(target) || target === 0) {
            counter.innerText = target;
            return;
        }
        
        const updateCount = () => {
            const current = +counter.innerText;
            const inc = target / speed;

            if (current < target) {
                counter.innerText = Math.ceil(current + inc);
                setTimeout(updateCount, 1);
            } else {
                counter.innerText = target + (counter.getAttribute('data-target').includes('.') ? '' : '');
            }
        };

        updateCount();
    });
}
