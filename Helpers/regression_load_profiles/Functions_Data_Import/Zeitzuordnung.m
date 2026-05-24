function [Zeitformat] = Zeitzuordnung(Jahr,Bundesland,Last,Feiertage_2000_bis_2050)
%% Zuordnung der Tagtypen anhand Wochen- Feier- und Sondertage (Brückentage)

Zeitformat = struct;

% Zeitvektor erstellen
if (numel(Last) == 35040 || numel(Last) == 35136)
    t1 = datetime(Jahr,1,1,0,0,0);
    t2 = datetime(Jahr,12,31,23,45,0);
    Zeitformat.Jahr = Jahr;
    Zeitformat.Time = transpose(t1:minutes(15):t2);
elseif (numel(Last) == 8760 || numel(Last) == 8784)
    t1 = datetime(Jahr,1,1,0,0,0);
    t2 = datetime(Jahr,12,31,23,00,0);
    Zeitformat.Jahr = Jahr;
    Zeitformat.Time = transpose(t1:hours(1):t2);
end

% Generieren des Monats- Wochen- und Tagvektors
    Zeitformat.Monat = categorical(month(Zeitformat.Time,'monthofyear'));
    Zeitformat.Woche = categorical(week(Zeitformat.Time,'weekofyear'));
    Zeitformat.Tag = categorical(day(Zeitformat.Time,'dayofyear'));

% Generierung der Tagtypvektoren
    % generiere Tagtypvektor mit 7 Tagtypen
    Zeitformat.Tagtyp_1_7_num = weekday(Zeitformat.Time) - 1;
    Zeitformat.Tagtyp_1_7_num(Zeitformat.Tagtyp_1_7_num < 1) = 7;
    
    % generiere Tagtypvektor mit 5 Tagtypen
    Zeitformat.Tagtyp_1_5_num = Zeitformat.Tagtyp_1_7_num;
    Zeitformat.Tagtyp_1_5_num(Zeitformat.Tagtyp_1_5_num == 3) = 2;
    Zeitformat.Tagtyp_1_5_num(Zeitformat.Tagtyp_1_5_num == 4) = 2;
    Zeitformat.Tagtyp_1_5_num(Zeitformat.Tagtyp_1_5_num == 5) = 3;
    Zeitformat.Tagtyp_1_5_num(Zeitformat.Tagtyp_1_5_num == 6) = 4;
    Zeitformat.Tagtyp_1_5_num(Zeitformat.Tagtyp_1_5_num == 7) = 5;

    % generiere Tagtypvektor mit 3 Tagtypen
    Zeitformat.Tagtyp_1_3_num = Zeitformat.Tagtyp_1_5_num;
    Zeitformat.Tagtyp_1_3_num(Zeitformat.Tagtyp_1_3_num == 2) = 1;
    Zeitformat.Tagtyp_1_3_num(Zeitformat.Tagtyp_1_3_num == 3) = 1;
    Zeitformat.Tagtyp_1_3_num(Zeitformat.Tagtyp_1_3_num == 4) = 2;
    Zeitformat.Tagtyp_1_3_num(Zeitformat.Tagtyp_1_3_num == 5) = 3;

    % generiere Tagtypvektor mit 1 Tagtyp
    Zeitformat.Tagtyp_1_1_num = Zeitformat.Tagtyp_1_3_num;
    Zeitformat.Tagtyp_1_1_num(Zeitformat.Tagtyp_1_1_num ~= 1) = 1;

%% Feier- und Brückentage auf Bundesebene zuordnen
index_start = Jahr - 1996;

% Bundesfeiertage zuordnen
for j = 1:numel(Feiertage_2000_bis_2050.Bundesland)
	if contains(Feiertage_2000_bis_2050.Bundesland(j),"DE")
		tlower(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start));
		tupper(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start)) + 0.9999;        
	end
end
for j = 1:numel(tlower)
	if tlower(j) ~= NaT
		Zeitformat.Feiertage(:,j) = isbetween(Zeitformat.Time,tlower(j,1),tupper(j,1));
	end
end
Feiertage = Zeitformat.Feiertage(:,1);
for j = 2:numel(tlower)
	Feiertage = or(Feiertage,Zeitformat.Feiertage(:,j));
end
Zeitformat.Feiertage = Feiertage;
for j = 1:numel(Feiertage)
	if Feiertage(j)
		Zeitformat.Tagtyp_1_7_num(j) = 7;
		Zeitformat.Tagtyp_1_5_num(j) = 5;
		Zeitformat.Tagtyp_1_3_num(j) = 3;
	end
end
clear tlower tupper Feiertage

% Brückentage zuordnen
num_Sondertage = 0;

for j = 1:numel(Feiertage_2000_bis_2050.Bundesland)
	if contains(Feiertage_2000_bis_2050.Bundesland(j),"DE")
		if day(table2array(Feiertage_2000_bis_2050(j,index_start)),"dayofweek") == 5
			tlower(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start)) + 1;
			tupper(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start)) + 1.9999;
			num_Sondertage = num_Sondertage + 1;
		end
	end
end
if num_Sondertage > 0
	for j = 1:numel(tlower)
		if tlower(j) ~= NaT
			Zeitformat.Sondertage(:,j) = isbetween(Zeitformat.Time,tlower(j,1),tupper(j,1));
		end
	end
	Sondertage = Zeitformat.Sondertage(:,1);
	for j = 2:numel(tlower)
		Sondertage = or(Sondertage,Zeitformat.Sondertage(:,j));
	end
	Zeitformat.Sondertage = Sondertage;
	for j = 1:numel(Sondertage)
		if Sondertage(j)
			Zeitformat.Tagtyp_1_7_num(j) = 6;
			Zeitformat.Tagtyp_1_5_num(j) = 4;
			Zeitformat.Tagtyp_1_3_num(j) = 2;
		end
	end
end
clear tlower tupper 

%% Feier- und Brückentage für Bundesland zuordnen
if Bundesland ~= "DE"

    num_Feiertage = 0;
	for j = 1:numel(Feiertage_2000_bis_2050.Bundesland)
		if contains(Feiertage_2000_bis_2050.Bundesland(j),Bundesland)
			tlower(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start));
			tupper(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start)) + 0.9999;  
            num_Feiertage = num_Feiertage + 1;
		end
    end
    if num_Feiertage > 0
	    for j = 1:numel(tlower)
		    if tlower(j) ~= NaT
			    Zeitformat.Feiertage(:,j) = isbetween(Zeitformat.Time,tlower(j,1),tupper(j,1));
		    end
	    end
	    Feiertage = Zeitformat.Feiertage(:,1);
	    for j = 2:numel(tlower)
		    Feiertage = or(Feiertage,Zeitformat.Feiertage(:,j));
	    end
	    Zeitformat.Feiertage = Feiertage;
	    for j = 1:numel(Feiertage)
		    if Feiertage(j)
			    Zeitformat.Tagtyp_1_7_num(j) = 7;
			    Zeitformat.Tagtyp_1_5_num(j) = 5;
			    Zeitformat.Tagtyp_1_3_num(j) = 3;
		    end
        end
    end
	clear tlower tupper Feiertage

	% Brückentage zuordnen
	num_Sondertage = 0;
	for j = 1:numel(Feiertage_2000_bis_2050.Bundesland)
		if contains(Feiertage_2000_bis_2050.Bundesland(j),Bundesland)
			if day(table2array(Feiertage_2000_bis_2050(j,index_start)),"dayofweek") == 5
				tlower(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start)) + 1;
				tupper(j,1) = table2array(Feiertage_2000_bis_2050(j,index_start)) + 1.9999;
				num_Sondertage = num_Sondertage + 1;
			end
		end
	end
	if num_Sondertage > 0
		for j = 1:numel(tlower)
			if tlower(j) ~= NaT
				Zeitformat.Sondertage(:,j) = isbetween(Zeitformat.Time,tlower(j,1),tupper(j,1));
			end
		end
		Sondertage = Zeitformat.Sondertage(:,1);
		for j = 2:numel(tlower)
			Sondertage = or(Sondertage,Zeitformat.Sondertage(:,j));
		end
		Zeitformat.Sondertage = Sondertage;
		for j = 1:numel(Sondertage)
			if Sondertage(j)
				Zeitformat.Tagtyp_1_7_num(j) = 6;
				Zeitformat.Tagtyp_1_5_num(j) = 4;
				Zeitformat.Tagtyp_1_3_num(j) = 2;
			end
		end
	end
	clear tlower tupper 
end

Zeitformat.Zeitindex_1_7 = Berechnung_Zeitindex(Zeitformat.Tagtyp_1_7_num);
Zeitformat.Zeitindex_1_5 = Berechnung_Zeitindex(Zeitformat.Tagtyp_1_5_num);
Zeitformat.Zeitindex_1_3 = Berechnung_Zeitindex(Zeitformat.Tagtyp_1_3_num);
Zeitformat.Zeitindex_1_1 = Berechnung_Zeitindex(Zeitformat.Tagtyp_1_1_num);

if (numel(Last) == 35040 || numel(Last) == 35136)
    Zeitformat.Time = Zeitformat.Time+"00:15:00";
end

Zeitformat.Uhrzeit = Zeitformat.Time;
Zeitformat.Uhrzeit.Format = "HH:mm";
Uhrzeit_str = string(Zeitformat.Uhrzeit);
Tagtyp_1_7_str = string(Zeitformat.Tagtyp_1_7_num);
Zeitformat.Tagtyp_1_7_categorical = categorical(append(Tagtyp_1_7_str,'-',Uhrzeit_str));

Tagtyp_1_5_str = string(Zeitformat.Tagtyp_1_5_num);
Zeitformat.Tagtyp_1_5_categorical = categorical(append(Tagtyp_1_5_str,'-',Uhrzeit_str));

Tagtyp_1_3_str = string(Zeitformat.Tagtyp_1_3_num);
Zeitformat.Tagtyp_1_3_categorical = categorical(append(Tagtyp_1_3_str,'-',Uhrzeit_str));

Tagtyp_1_1_str = string(Zeitformat.Tagtyp_1_1_num);
Zeitformat.Tagtyp_1_1_categorical = categorical(append(Tagtyp_1_1_str,'-',Uhrzeit_str));
clear Tagtyp_1_7_str Tagtyp_1_5_str Tagtyp_1_3_str Tagtyp_1_1_str Uhrzeit_str Uhrzeit


function Zeit_Index = Berechnung_Zeitindex(Tagtyp)

    if (numel(Tagtyp) == 35040 || numel(Tagtyp) == 35136)
        num_values_std = 4;
    elseif (numel(Tagtyp) == 8760 || numel(Tagtyp) == 8784)
        num_values_std = 1;
    end
	
	% Länge des Jahres ermitteln
	l = size(Tagtyp,1);
	m = l / (24*num_values_std);
	
	% Berechnung des Zeitindexes für die 15-Minutenwerte an einem Tag von 1 bis 96
	k = 0;
	Uhrzeit_Num = zeros(l,1);
	for i = 1:m
		for j = 1:(24*num_values_std)
			k = k+1;
			Uhrzeit_Num(k) = j;
		end
	end
	
	% Zuordnen des Zeitindex
	Zeit_Index = zeros(l,1);
	for i = 1:l
		switch Tagtyp(i)
			case 1
				Zeit_Index(i) = Uhrzeit_Num(i);
			case 2
				Zeit_Index(i) = Uhrzeit_Num(i) + 24 * num_values_std;
			case 3
				Zeit_Index(i) = Uhrzeit_Num(i) + 48  *num_values_std;
			case 4
				Zeit_Index(i) = Uhrzeit_Num(i) + 72 * num_values_std;
			case 5
				Zeit_Index(i) = Uhrzeit_Num(i) + 96 * num_values_std;
			case 6
				Zeit_Index(i) = Uhrzeit_Num(i) + 120 * num_values_std;
			case 7
				Zeit_Index(i) = Uhrzeit_Num(i) + 144 * num_values_std;
			otherwise
				warning('Tagtyp fehlerhaft');
		end
	end
end

end