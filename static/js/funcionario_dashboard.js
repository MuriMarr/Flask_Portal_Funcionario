document.addEventListener("DOMContentLoaded", () => {
    const data = window.funcionarioData;

    const ctxHoras = document.getElementById("graficoHoras");
    const ctxExtras = document.getElementById("graficoExtras");

    new Chart(ctxHoras, {
        type: "line",
        data: {
            labels: data.semanas,
            datasets: [{
                label: "Horas Trabalhadas",
                data: data.horas_semanais,
                borderColor: "rgba(54, 162, 235, 1)",
                backgroundColor: "rgba(54, 162, 235, 0.2)",
                tension: 0.3,
                fill: true
            }]
        }
    });

    new Chart(ctxExtras, {
        type: "bar",
        data: {
            labels: data.semanas,
            datasets: [{
                label: "Horas Extras",
                data: data.extras_semanais,
                backgroundColor: "rgba(255, 99, 132, 0.6)",
                borderColor: "rgba(255, 99, 132, 1)",
                borderWidth: 1
            }]
        }
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const btnRegistrar = document.getElementById("registrarPonto");

    if (btnRegistrar) {
        btnRegistrar.addEventListener("click", function () {
            const agora = new Date();

            fetch(btnRegistrar.dataset.url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    data: agora.toISOString().split("T")[0],
                    hora: agora.toTimeString().split(" ")[0]
                })
            })
            .then(res => {
                if (res.redirected) {
                    window.location.href = res.url;
                } else {
                    window.location.reload();
                }
            })
            .catch(err => console.error("Erro ao registrar ponto:", err));
        });
    }
});