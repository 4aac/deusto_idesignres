function Branchen_vs_Einzel(Branchenmodell,Referenzzeitreihen,Branche_name)

Branche = Branchenmodell.Referenzzeitreihen.Lastgang;

Einzel = Referenzzeitreihen(1).Zeitreihe_normiert.Lastgang;
for j = 2:numel(Referenzzeitreihen)
    Einzel = cat(2,Einzel,Referenzzeitreihen(j).Zeitreihe_normiert.Lastgang);
end
YMatrix = cat(2,Einzel,Branche);
Time = Branchenmodell.Referenzzeitreihen.Time;

% Create figure
figure1 = figure;

% Create axes
axes1 = axes('Parent',figure1);
hold(axes1,'on');

% Create multiple line objects using matrix input to plot
plot1 = plot(Time,YMatrix,'Parent',axes1);

str1 = "Einzelmodell ";
for i = 1:numel(Referenzzeitreihen)
    str2 = num2str(Referenzzeitreihen(i).Standort);
    str3 = append(str1,str2);
    str3 = char(str3);
    set(plot1(i),'DisplayName',str3);
end
set(plot1(i+1),'DisplayName','Branchenmodell','LineWidth',2,'Color',[0 0 0]);

% Create title
str = "Branchenmodell vs. Einzelmodelle - ";
str_title = append(str,Branche_name);
str_title = char(str_title);
title({str_title});

% limits of y-axis
max_yval = max(YMatrix,[],'all')*1.1;
ylim(axes1,[0 max_yval]);

box(axes1,'on');
hold(axes1,'off');
legend(axes1,'show');
