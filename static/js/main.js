/**
 * LifeDrop BD - Main Client-Side Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Cascading District -> Upazila Dropdown Loader
    const districtSelects = document.querySelectorAll('select[data-upazila-target]');
    districtSelects.forEach(function (distSelect) {
        const targetId = distSelect.getAttribute('data-upazila-target');
        const upazilaSelect = document.getElementById(targetId);

        if (upazilaSelect) {
            distSelect.addEventListener('change', function () {
                const districtId = this.value;
                if (!districtId) {
                    upazilaSelect.innerHTML = '<option value="">-- All Upazilas --</option>';
                    return;
                }

                fetch(`/api/upazilas/?district_id=${districtId}`)
                    .then(response => response.json())
                    .then(data => {
                        let options = '<option value="">-- All Upazilas --</option>';
                        data.upazilas.forEach(uz => {
                            options += `<option value="${uz.id}">${uz.name}</option>`;
                        });
                        upazilaSelect.innerHTML = options;
                    })
                    .catch(err => console.error('Error fetching upazilas:', err));
            });
        }
    });

    // 2. Auto-hide Bootstrap alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // 3. Mark notification as read
    const notifPills = document.querySelectorAll('.mark-read-btn');
    notifPills.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const notifId = this.getAttribute('data-id');
            fetch(`/notifications/${notifId}/mark-read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const row = document.getElementById(`notif-row-${notifId}`);
                    if (row) {
                        row.classList.remove('bg-light');
                        row.classList.add('text-muted');
                    }
                    this.remove();
                }
            });
        });
    });
});

// CSRF helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
