(function () {
    function getCookie(name) {
        const cookies = document.cookie.split(";");

        for (const cookie of cookies) {
            const [key, ...value] = cookie.trim().split("=");

            if (key === name) {
                return decodeURIComponent(value.join("="));
            }
        }

        return null;
    }

    window.uploadImage = function (blobInfo, progress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.open("POST", "/tinymce/upload-image/");

            const csrfToken = getCookie("csrftoken");

            if (csrfToken) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            }

            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    progress((event.loaded / event.total) * 100);
                }
            };

            xhr.onload = function () {
                if (xhr.status < 200 || xhr.status >= 300) {
                    reject("HTTP Error: " + xhr.status);
                    return;
                }

                let json;

                try {
                    json = JSON.parse(xhr.responseText);
                } catch (error) {
                    reject("Réponse invalide du serveur.");
                    return;
                }

                if (!json || typeof json.location !== "string") {
                    reject("La réponse ne contient pas de location.");
                    return;
                }

                resolve(json.location);
            };

            xhr.onerror = function () {
                reject("Erreur réseau pendant l'upload.");
            };

            const formData = new FormData();

            formData.append(
                "file",
                blobInfo.blob(),
                blobInfo.filename()
            );

            xhr.send(formData);
        });
    };
})();