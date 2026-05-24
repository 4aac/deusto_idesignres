function Synthetisierung_Plot(Lastprofile_normiert)
%CREATEFIGURE(XMatrix1, YMatrix1, YMatrix2, YMatrix3)
%  XMATRIX1:  matrix of plot x data
%  YMATRIX1:  matrix of plot y data
%  YMATRIX2:  matrix of plot y data
%  YMATRIX3:  matrix of plot y data

XMatrix1 = Lastprofile_normiert.Time;
YMatrix1(:,1) = Lastprofile_normiert.Lastprofil_norm_JV_mean;
YMatrix1(:,2) = Lastprofile_normiert.Lastprofil_norm_JV_005;
YMatrix1(:,3) = Lastprofile_normiert.Lastprofil_norm_JV_095;

YMatrix2(:,1) = Lastprofile_normiert.Lastprofil_norm_M_mean;
YMatrix2(:,2) = Lastprofile_normiert.Lastprofil_norm_M_005;
YMatrix2(:,3) = Lastprofile_normiert.Lastprofil_norm_M_095;

YMatrix3(:,1) = Lastprofile_normiert.Lastprofil_norm_F_mean;
YMatrix3(:,2) = Lastprofile_normiert.Lastprofil_norm_F_005;
YMatrix3(:,3) = Lastprofile_normiert.Lastprofil_norm_F_095;

% Create figure
figure1 = figure;

% Create subplot
subplot1 = subplot(3,1,1,'Parent',figure1);
hold(subplot1,'on');

% Create multiple line objects using matrix input to plot
plot1 = plot(XMatrix1,YMatrix1,'Parent',subplot1);
set(plot1(1),'DisplayName','Mittelwert',...
    'Color',[0 0.447058826684952 0.74117648601532]);
set(plot1(2),'DisplayName','Konfidenzintervall 5 % Grenze','Color',[0 0.498039215803146 0]);
set(plot1(3),'DisplayName','Konfidenzintervall 95 % Grenze',...
    'Color',[0.635294139385223 0.0784313753247261 0.184313729405403]);

% Create ylabel
ylabel('normiert nach Jahresverbrauch');

box(subplot1,'on');
hold(subplot1,'off');
% Create legend
legend1 = legend(subplot1,'show');
set(legend1,...
    'Position',[0.4513671875 0.929419535311126 0.132682291666667 0.0191292875989446],...
    'Orientation','horizontal');

% Create subplot
subplot2 = subplot(3,1,2,'Parent',figure1);
hold(subplot2,'on');

% Create multiple line objects using matrix input to plot
plot2 = plot(XMatrix1,YMatrix2,'Parent',subplot2);
set(plot2(1),'Color',[0 0.447058826684952 0.74117648601532]);
set(plot2(2),'Color',[0 0.498039215803146 0]);
set(plot2(3),...
    'Color',[0.635294139385223 0.0784313753247261 0.184313729405403]);

% Create ylabel
ylabel('normiert nach Mitarbeiterzahl');

box(subplot2,'on');
hold(subplot2,'off');
% Create subplot
subplot3 = subplot(3,1,3,'Parent',figure1);
hold(subplot3,'on');

% Create multiple line objects using matrix input to plot
plot3 = plot(XMatrix1,YMatrix3,'Parent',subplot3);
set(plot3(1),'Color',[0 0.447058826684952 0.74117648601532]);
set(plot3(2),'Color',[0 0.498039215803146 0]);
set(plot3(3),...
    'Color',[0.635294139385223 0.0784313753247261 0.184313729405403]);

% Create ylabel
ylabel('normiert nach Produktionsfläche');

box(subplot3,'on');
hold(subplot3,'off');
