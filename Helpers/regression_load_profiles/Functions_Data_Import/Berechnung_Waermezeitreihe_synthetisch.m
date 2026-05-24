function [Waermezeitreihe_stuendlich] = Berechnung_Waermezeitreihe_synthetisch(Time,Waermebedarf,Temperatur,Tagtyp_1_7,GasprofilNr,Gasprofile,SV_Tabelle)
%% Erstellung GHD Gasprofil nach BDEW Leitfaden

Tagtyp = char(Tagtyp_1_7);
Tagtyp = str2num(Tagtyp(:,1));

% Parameter_Waerme = struct;

% Zuordnung in Dokumentation gelistet
% hier: gemitteltes Profil "DE_GBD"
GasprofilNr = GasprofilNr;

% Jahresverbrauch in kWh
Jahresverbrauch = Waermebedarf;			

% Angabe, ob eigene Temperaturzeitreihe, oder gemittelte DE Zeitreihe
% 0: eigene Zeitreihe einfügen, sonst Index aus "DE_Klima" eingeben
Zeitreihe_Nr = 0; 

% eigene Zeitreihe als timetable in stündlicher Form
% (siehe Bsp. für Format)
%eigene_Zeitreihe = eigene_Zeitreihe_Bsp;

%% restliche Parameter
varNames = ["Temperatur","Tagtyp"];
Zeitreihe_stuendlich = timetable(Time,Temperatur,Tagtyp,'VariableNames',varNames);
Zeitreihe_taeglich = retime(Zeitreihe_stuendlich, 'daily', 'mean');
theta = Zeitreihe_taeglich.Temperatur;	% Außentemperaturvektor

% Tagesmitteltemperatur der letzten drei Tage des Vorjahres eintragen:
T_mittel_Vorjahr = [theta(1) theta(1) theta(1)];

Tagtyp = Zeitreihe_taeglich.Tagtyp;	% Tagtypenvektor für Standort


%% Berechnungen nach BDEW/VKU/GEODE Leitfaden "Abwicklung von Standardlastprofilen Gas"
% Berechnung der Allokationstemperatur

T_D = zeros(numel(theta)+3,1);

T_D(1) = T_mittel_Vorjahr(1);
T_D(2) = T_mittel_Vorjahr(2);
T_D(3) = T_mittel_Vorjahr(3);

for i = 1:numel(Tagtyp)
	T_D(i+3) = Zeitreihe_taeglich.Temperatur(i);
end
T_Allokation = zeros(numel(Zeitreihe_taeglich.Temperatur),1);

for i = 1:numel(T_Allokation)
    if isnan(T_D(i+2)) & isnan(T_D(i+1)) & isnan(T_D(i)) 
        T_D(i+2) = T_D(i+3);
        T_D(i+1) = T_D(i+3);
        T_D(i) = T_D(i+3);
    end
	T_Allokation(i) = (T_D(i+3) + 0.5 * T_D(i+2) + 0.25 * T_D(i+1) + 0.125 * T_D(i))/(1 + 0.5 + 0.25 + 0.125);
end
Fehldaten = isnan(T_Allokation);
theta = T_Allokation;
theta(Fehldaten==1,:) = [];

% Profilkoeffizienten zurodnen

Gasprofil = Gasprofile(GasprofilNr).Werte;

% Wochentagsfaktoren dem Vektor F_WT zuordnen

MO = Gasprofil(10);
DI = Gasprofil(11);
MI = Gasprofil(12);
DO = Gasprofil(13);
FR = Gasprofil(14);
SA = Gasprofil(15);
SO = Gasprofil(16);

% Wochentagfaktoren den Tagtypen zuordnen:
F_WT = zeros(size(Tagtyp,1),1);

F_WT(Tagtyp==1) = MO;
F_WT(Tagtyp==2) = DI;
F_WT(Tagtyp==3) = MI;
F_WT(Tagtyp==4) = DO;
F_WT(Tagtyp==5) = FR;
F_WT(Tagtyp==6) = SA;
F_WT(Tagtyp==7) = SO;

if F_WT(Tagtyp==0)
    error("Fehler bei Tagtypen!");
end
F_WT(Fehldaten==1,:) = [];
Tagtyp(Fehldaten==1,:) = [];

% Berechnung von h(theta)

A = Gasprofil(1);
B = Gasprofil(2);
C = Gasprofil(3);
D = Gasprofil(4);
theta_0 = Gasprofil(5);
m_H = Gasprofil(6);
b_H = Gasprofil(7);
m_W = Gasprofil(8);
b_W = Gasprofil(9);

% Berechnung von h(theta)

h_theta_val = h_theta(theta,A,B,C,D,theta_0,m_H,b_H,m_W,b_W);

% Berechnung des Kundenwerts KW

KW = (Jahresverbrauch)/(sum(h_theta_val.*F_WT));

% Berechnung von Q_Allokation

Q_Allokation = KW * h_theta_val.* F_WT;

%% Umrechnung von täglicher auf stündliche Auflösung

% Stundenverteilung aus Tabelle zuordnen

SV = SV_Zuordnung(GasprofilNr,Tagtyp,theta,h_theta_val,SV_Tabelle);

Q_Allokation_std = zeros(numel(h_theta_val)*24,1);

k = 0;
for i = 1:numel(Tagtyp)
	for j = 1:24
		Q_Allokation_std(k+j) = Q_Allokation(i);
	end
	k = k+24;
end

% Gaszeitreihe in stündlicher Auflösung erstellen

Q_Stunde = zeros(numel(h_theta_val)*24,1);

for i = 1:numel(Q_Allokation_std)
    Q_Stunde(i) = Q_Allokation_std(i)*((SV(i))/100);
end

% Ausgabe der Zeitreihe

Q_Stunde = Q_Stunde * (Waermebedarf)/(sum(Q_Stunde));
% Waermezeitreihe_stuendlich = Q_Stunde;
varNames = ["Waerme","Temperatur","Tagtyp_1_7"];
Waermezeitreihe_stuendlich = timetable(Zeitreihe_stuendlich.Time, Q_Stunde, Zeitreihe_stuendlich.Temperatur,Tagtyp_1_7,'VariableNames',varNames);

%% h_theta als nested function:
function h_theta = h_theta(theta,A,B,C,D,theta_0,m_H,b_H,m_W,b_W)
    % Berechnung von h(theta)
    h_theta = zeros(numel(theta),1);
    for index_h_theta = 1:numel(theta)
        h_theta(index_h_theta,1) = (A/((1+(B/(theta(index_h_theta)-theta_0))).^C))+D + (max((m_H*theta(index_h_theta)+b_H),(m_W*theta(index_h_theta)+b_W)));
    end
end

%% SV Zuordnung als nested function:
function SV = SV_Zuordnung(GasprofilNr,Tagtyp,T_Allokation,h_theta,SV_Tabelle)
    % Stundenverteilung aus Tabelle zuordnen
    SV = zeros(numel(h_theta)*24,1);
    index_k_SV = 0;
    for index_i_SV = 1:numel(Tagtyp)
        % Montag
		if Tagtyp(index_i_SV) == 1
			if T_Allokation(index_i_SV) < -15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(1,index_j_SV);
				end
			elseif (T_Allokation(index_i_SV) >= -15) && (T_Allokation(index_i_SV) < -10)
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(2,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -10 && T_Allokation(index_i_SV) < -5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(3,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -5 && T_Allokation(index_i_SV) < 0
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(4,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 0 && T_Allokation(index_i_SV) < 5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(5,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 5 && T_Allokation(index_i_SV) < 10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(6,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 10 && T_Allokation(index_i_SV) < 15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(7,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 15 && T_Allokation(index_i_SV) < 20
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(8,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 20 && T_Allokation(index_i_SV) < 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(9,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) > 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Montag(10,index_j_SV);
                end
            end

        % Dienstag
		elseif Tagtyp(index_i_SV) == 2
			if T_Allokation(index_i_SV) < -15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(1,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -15 && T_Allokation(index_i_SV) < -10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(2,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -10 && T_Allokation(index_i_SV) < -5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(3,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -5 && T_Allokation(index_i_SV) < 0
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(4,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 0 && T_Allokation(index_i_SV) < 5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(5,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 5 && T_Allokation(index_i_SV) < 10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(6,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 10 && T_Allokation(index_i_SV) < 15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(7,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 15 && T_Allokation(index_i_SV) < 20
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(8,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 20 && T_Allokation(index_i_SV) < 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(9,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) > 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Dienstag(10,index_j_SV);
				end
            end

        % Mittwoch
        elseif Tagtyp(index_i_SV) == 3
			if T_Allokation(index_i_SV) < -15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(1,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -15 && T_Allokation(index_i_SV) < -10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(2,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -10 && T_Allokation(index_i_SV) < -5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(3,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -5 && T_Allokation(index_i_SV) < 0
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(4,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 0 && T_Allokation(index_i_SV) < 5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(5,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 5 && T_Allokation(index_i_SV) < 10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(6,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 10 && T_Allokation(index_i_SV) < 15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(7,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 15 && T_Allokation(index_i_SV) < 20
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(8,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 20 && T_Allokation(index_i_SV) < 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(9,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) > 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Mittwoch(10,index_j_SV);
				end
            end
        
        % Donnerstag
        elseif Tagtyp(index_i_SV) == 4
			if T_Allokation(index_i_SV) < -15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(1,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -15 && T_Allokation(index_i_SV) < -10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(2,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -10 && T_Allokation(index_i_SV) < -5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(3,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -5 && T_Allokation(index_i_SV) < 0
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(4,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 0 && T_Allokation(index_i_SV) < 5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(5,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 5 && T_Allokation(index_i_SV) < 10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(6,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 10 && T_Allokation(index_i_SV) < 15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(7,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 15 && T_Allokation(index_i_SV) < 20
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(8,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 20 && T_Allokation(index_i_SV) < 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(9,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) > 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Donnerstag(10,index_j_SV);
				end
            end

        % Freitag
        elseif Tagtyp(index_i_SV) == 5
			if T_Allokation(index_i_SV) < -15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(1,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -15 && T_Allokation(index_i_SV) < -10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(2,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -10 && T_Allokation(index_i_SV) < -5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(3,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -5 && T_Allokation(index_i_SV) < 0
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(4,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 0 && T_Allokation(index_i_SV) < 5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(5,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 5 && T_Allokation(index_i_SV) < 10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(6,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 10 && T_Allokation(index_i_SV) < 15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(7,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 15 && T_Allokation(index_i_SV) < 20
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(8,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 20 && T_Allokation(index_i_SV) < 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(9,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) > 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Freitag(10,index_j_SV);
				end
            end
        
        % Samstag
		elseif Tagtyp(index_i_SV) == 6
			if T_Allokation(index_i_SV) < -15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(1,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -15 && T_Allokation(index_i_SV) < -10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(2,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -10 && T_Allokation(index_i_SV) < -5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(3,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -5 && T_Allokation(index_i_SV) < 0
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(4,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 0 && T_Allokation(index_i_SV) < 5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(5,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 5 && T_Allokation(index_i_SV) < 10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(6,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 10 && T_Allokation(index_i_SV) < 15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(7,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 15 && T_Allokation(index_i_SV) < 20
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(8,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 20 && T_Allokation(index_i_SV) < 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(9,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) > 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Samstag(10,index_j_SV);
				end
            end

        % Sonn- und Feiertag
		elseif Tagtyp(index_i_SV) == 7
			if T_Allokation(index_i_SV) < -15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(1,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -15 && T_Allokation(index_i_SV) < -10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(2,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -10 && T_Allokation(index_i_SV) < -5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(3,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= -5 && T_Allokation(index_i_SV) < 0
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(4,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 0 && T_Allokation(index_i_SV) < 5
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(5,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 5 && T_Allokation(index_i_SV) < 10
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(6,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 10 && T_Allokation(index_i_SV) < 15
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(7,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 15 && T_Allokation(index_i_SV) < 20
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(8,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) >= 20 && T_Allokation(index_i_SV) < 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(9,index_j_SV);
				end
			elseif T_Allokation(index_i_SV) > 25
				for index_j_SV = 1:24
					SV(index_k_SV+index_j_SV) = SV_Tabelle(GasprofilNr).Sonntag(10,index_j_SV);
				end
			end
		end
	    index_k_SV = index_k_SV+24;
    end
end


end