function success_alert(msg) {
    Swal.fire({
        title: '',
        text: msg,
        icon: 'success',
        background: '#1e293b',
        color: '#f1f5f9',
        confirmButtonColor: '#3b82f6',
        timer: 2000, // 弹窗显示 2 秒
        showConfirmButton: false, // 不显示确认按钮
    });
}

function error_alert(msg) {
    Swal.fire({
        title: '',
        text: msg,
        icon: 'error',
        background: '#1e293b',
        color: '#f1f5f9',
        confirmButtonColor: '#3b82f6',
        timer: 2000, // 弹窗显示 2 秒
        showConfirmButton: false, // 不显示确认按钮
    });
}