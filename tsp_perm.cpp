#include <bits/stdc++.h>
using namespace std;
using namespace chrono;

/*
Realiza todas as permutacoes de caminhos do TSP euclideano em O(n!)
*/

class timer: high_resolution_clock {
    const time_point start_time;
public:
    timer(): start_time(now()) {}
    rep elapsed_time() const { return duration_cast<milliseconds>(now()-start_time).count(); } };

// Ler o vetor de cordenadas
std::vector<std::pair<double, double>> readCSV(const std::string& path) {
    vector<std::pair<double, double>> points;
    ifstream file(path);
    string line;

    while (std::getline(file, line)) {
        stringstream ss(line);
        string xs, ys;
        if (std::getline(ss, xs, ',') && std::getline(ss, ys)) {
            points.emplace_back(std::stod(xs), std::stod(ys));
        }
    }
    return points;
}


//calculo da distancia euclidiana entre dois pontos
double dist(const pair<double, double>& a, const pair<double, double>& b) {
    return std::hypot(a.first - b.first, a.second - b.second);
}

//define uma distancia inicial arbitrariamente grande que precisa ser diminuida
double min_dist = 1e12;
vector<int> final_path;

//backtracking testando todas as permutacoes recursivamente
void all_permutations(vector<pair<double, double>>& points, vector<int>& path, int pt_size, double total_dist){
    if((int)path.size() == pt_size){

        total_dist += dist(points[0], points[path.back()]);

        if(total_dist < min_dist){
            min_dist = total_dist;
            final_path = path;
        }

        return;
    }

    vector<bool>visited(pt_size, false);

    for(auto x: path){
        visited[x] = true;
    }

    for(int i = 0; i < pt_size; i++){
        if(!visited[i]){
            total_dist += dist(points[i], points[path.back()]);
            path.push_back(i);

            all_permutations(points, path, pt_size, total_dist);

            path.pop_back();
            total_dist -= dist(points[i], points[path.back()]);
        }
    }
}

int main(){
    timer t;

    vector<std::pair<double, double>> points = readCSV("../burma14.csv");
    int points_size = (int)points.size();
    vector<int>path;
    path.push_back(0);
    all_permutations(points, path, points_size, 0);

    cout << min_dist << '\n';
    for(auto x: final_path){
        cout << x << ' ';
    }
    cout << '\n';

    cout << t.elapsed_time() << '\n';
}