document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll(".saldo-cell").forEach(cell => {
        const text = cell.innerText.trim();
        const match = text.match(/(-?\d+)h (\d+)min/);
        if (!match) return;

        const horas = parseInt(match[1], 10);
        const minutos = parseInt(match[2], 10);
        const totalMinutos = horas * 60 + minutos;

        let tipo = cell.dataset.tipo;

        switch (tipo) {
            case "saldo":
                if (totalMinutos > 0) {
                    cell.classList.add("positivo");
                } else if (totalMinutos < 0) {
                    cell.classList.add("negativo");
                } else {
                    cell.classList.add("neutro");
                }
                break;
            
            case "horas":
            cell.classList.add("neutro");
                break;
            
            case "extras":
                if (totalMinutos > 0) cell.classList.add("positivo");
                else cell.classList.add("neutro");
                break;

            case "deficit":
                if (totalMinutos > 0) cell.classList.add("negativo");
                else cell.classList.add("neutro");
                break;
        }
    });
});