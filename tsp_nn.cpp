#include <bits/stdc++.h>
using namespace std;
using namespace chrono;

/*
Algoritmo de Nearest Neighbor para TSP euclideano

O algoritmo para um ponto de partida roda em O(n^2), 
porem, como o resultado é fortemente influenciado pelo
ponto de partida, testamos todas as possibilidades, 
transformando o algoritmo em O(n^3).
Entao, para instancias acima de 1000 pontos o algoritmo
demorara um pouco para rodar. Ele poderia ser otimizado 
com estruturas de dados mais sofisticadas, como KD-trees.

COMO USAR:

dentro da main coloque o caminho para o arquivo csv
que contem os dados, apos isso ele criara o arquivo 
saida com os resultados
*/

// Classe para cronometrar o tempo de execucao em milisegundos
class timer: high_resolution_clock {
    const time_point start_time;
public:
    timer(): start_time(now()) {}
    rep elapsed_time() const { return duration_cast<milliseconds>(now()-start_time).count(); } };


std::vector<std::pair<double, double>> readCSV(const std::string& path) {
    vector<std::pair<double, double>> points;
    ifstream file(path);
    string line;

    while (std::getline(file, line)) {
        stringstream ss(line);
        string xs, ys;
        //!!!!!Se o CSV for separado por tab coloque '\t', e se for por virgula ','.
        //Eu queria automatizar isso para detectar automatico, mas nao sei como :(
        if (std::getline(ss, xs, ',') && std::getline(ss, ys)) {
            points.emplace_back(std::stod(xs), std::stod(ys));
        }
    }
    return points;
}


int main(){
    timer tempo;

    // ALTERAR ARQUIVOS DE ENTRADA E SAIDA!!!!
    const string arquivo_entrada = "../datasets/u1060.csv";
    const string arquivo_saida = "../resultado_nn_u1060.csv";

    ofstream out(arquivo_saida);
    out << fixed << setprecision(6);
    out << "inicio,distancia,caminho\n";

    //Para manter as melhores e piores distancias globais
    double best_dist = 1e12;
    double worst_dist = 0;

    vector<std::pair<double, double>> points = readCSV(arquivo_entrada);

    int points_size = (int)points.size();
    cout << "Tamnho da instancia carregada: " << points_size << '\n';

    vector<vector<double>>matriz_distancias(points_size, vector<double>(points_size));

    for(int i = 0; i < points_size; i++){
        for(int j = i; j < points_size; j++){
            matriz_distancias[i][j] = sqrt(pow(points[i].first - points[j].first, 2) + pow(points[i].second - points[j].second, 2));
            matriz_distancias[j][i] = matriz_distancias[i][j];
        }
    }

    for(int inicio = 0; inicio < points_size; inicio++){

        vector<int>caminho;
        vector<bool>visitado(points_size, false);
    
        caminho.push_back(inicio);

        double dist = 0;

        for(int i = 1 ; i < points_size; i++){
            int vert = caminho.back();
            visitado[vert] = true;

            double min_dist = 1e12;
            int idx_min_point;

            for(int j = 0; j < points_size; j++){
                if(!visitado[j]){
                    if(matriz_distancias[vert][j] < min_dist){
                        min_dist = matriz_distancias[vert][j];
                        idx_min_point = j;
                    }
                }
            }

            dist += min_dist;
            caminho.push_back(idx_min_point);
        }

        dist += matriz_distancias[caminho.back()][inicio];

        out << inicio << ',' << dist << ',';
        for(int i = 0; i < points_size; i++){
            if(i > 0) out << ' ';
            out << caminho[i];
        }
        out << '\n';
    
        best_dist = min(best_dist, dist);
        worst_dist = max(worst_dist, dist);
    }


    cout << best_dist << ' ' << worst_dist << '\n';

    cout << "Tempo de execucao: " << tempo.elapsed_time() << '\n';
}