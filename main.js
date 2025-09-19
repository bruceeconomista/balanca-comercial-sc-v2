document.addEventListener('DOMContentLoaded', () => {
    const yearSelect = document.getElementById('year-select');

    // Função para carregar os dados e renderizar os gráficos
    const updateCharts = async (year) => {
        try {
            // Carrega os dados de exportação
            const expProductsResponse = await fetch(`static_data/exp_products_${year}.json`);
            const expProductsData = await expProductsResponse.json();

            const expCountriesResponse = await fetch(`static_data/exp_countries_${year}.json`);
            const expCountriesData = await expCountriesResponse.json();

            // Carrega os dados de importação
            const impProductsResponse = await fetch(`static_data/imp_products_${year}.json`);
            const impProductsData = await impProductsResponse.json();

            const impCountriesResponse = await fetch(`static_data/imp_countries_${year}.json`);
            const impCountriesData = await impCountriesResponse.json();

            // Renderiza os gráficos
            renderBarChart('exp-products-chart', expProductsData, 'NO_NCM_POR', 'VL_FOB', `Produtos Mais Exportados (${year})`);
            renderBarChart('exp-countries-chart', expCountriesData, 'NO_PAIS', 'VL_FOB', `Países de Destino (Exportação) (${year})`);
            renderBarChart('imp-products-chart', impProductsData, 'NO_NCM_POR', 'VL_FOB', `Produtos Mais Importados (${year})`);
            renderBarChart('imp-countries-chart', impCountriesData, 'NO_PAIS', 'VL_FOB', `Países de Origem (Importação) (${year})`);

        } catch (error) {
            console.error("Erro ao carregar ou renderizar os dados:", error);
        }
    };

    // Função genérica para renderizar gráficos de barra
    const renderBarChart = (elementId, data, xKey, yKey, title) => {
        const xValues = data.map(item => item[xKey]);
        const yValues = data.map(item => item[yKey]);

        const trace = {
            x: xValues,
            y: yValues,
            type: 'bar',
            marker: {
                color: '#3f51b5' // Cor principal
            }
        };

        const layout = {
            title: title,
            font: {
                family: 'Arial, sans-serif'
            },
            xaxis: {
                title: 'Item',
                tickangle: -45,
                automargin: true
            },
            yaxis: {
                title: 'Valor FOB (US$)',
                tickformat: '$,s' // Formata para notação de milhar/milhão
            }
        };

        const config = { responsive: true };
        
        Plotly.newPlot(elementId, [trace], layout, config);
    };

    // Evento para atualizar os gráficos quando o ano for selecionado
    yearSelect.addEventListener('change', (event) => {
        const selectedYear = event.target.value;
        updateCharts(selectedYear);
    });

    // Carrega os gráficos iniciais com o ano padrão (2024)
    updateCharts(yearSelect.value);
});