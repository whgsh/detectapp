// 当本地视频文件选择后，自动填充URL输入框
function updateURLField() {
    var fileInput = document.getElementById('local_video');
    var urlInput = document.getElementById('url');
    if (fileInput.files.length > 0) {
        var file = fileInput.files[0];
        urlInput.value = URL.createObjectURL(file);
    }
}