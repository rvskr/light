document.querySelector('.buy').addEventListener('click', function() {
    alert('Программа полностью бесплатная!');  // Показываем сообщение о бесплатности программы
});


document.querySelector('.download').addEventListener('click', function() {
    fetch('https://api.github.com/repos/rvskr/light/releases/latest')
        .then(response => response.json())
        .then(data => {
            const exeAsset = data.assets.find(asset => asset.name.endsWith('.exe'));
            if (exeAsset) {
                window.location.href = exeAsset.browser_download_url;
            } else {
                alert('Извините, .exe файл не найден в последнем релизе.');
            }
        })
        .catch(error => {
            console.error('Ошибка при получении данных о релизе:', error);
            alert('Произошла ошибка при попытке скачать файл. Пожалуйста, попробуйте позже.');
        });
});