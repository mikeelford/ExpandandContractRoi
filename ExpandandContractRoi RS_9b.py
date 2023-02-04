# encoding: utf8
# !/usr/bin/python
# ------------------------------------------------------
# Name:        Expand&ContractRoi
# Purpose:     3D ROI rounding tool
# Author:      M. Elford
# Created:     16-11-2018 for RS vs 7.0
# ------------------------------------------------------

import wpf
import clr
import sys

sys.path.append(r'C:\Program Files\RaySearch Laboratories\RayStation 9B')

clr.AddReference('System')
clr.AddReference("System.Xml")
# Run in RayStation.
from connect import *
from System.Windows import *
from System.Windows.Controls import *
from System.IO import StringReader
from System.Xml import XmlReader


def GetPlan():
    # ###########################################
    # ##  Code to get handles to plan data   ####
    # ###########################################
    global case, plan, exam, examination, ss
    try:
        case = get_current('Case')
        examination = get_current('Examination')
        ss = case.PatientModel.StructureSets[examination.Name]
    except:
        MessageBox.Show('A patient and plan must be loaded.', "Expand&ContractRoi", MessageBoxButton.OK,
                        MessageBoxImage.Information)
        sys.exit()


def UniqueRoi(name, fss):
    for p in fss.RoiGeometries:
        if name == p.OfRoi.Name:
            name = f'{name}_1'
            name = UniqueRoi(name, fss)
    return name


class MyWindow(Window):
    def __init__(self):
        # Load xaml component.
        self.xaml = xaml()
        xr = XmlReader.Create(StringReader(self.xaml.xaml))
        wpf.LoadComponent(self, xr)
        # Get the ROIs.
        roi_list = [roi.OfRoi.Name for roi in ss.RoiGeometries if roi.HasContours()]
        self.SelectROI.ItemsSource = roi_list

    def ComputeClicked(self, sender, event):
        # Get the ROI from the combobox.
        RoiName = self.SelectROI.SelectedItem

        if RoiName in ["", 'None']:
            # No ROI selected
            MessageBox.Show('First choose an ROI.', "Expand&ContractRoi", MessageBoxButton.OK,
                            MessageBoxImage.Information)
            return

        margin = self.slValue.Value

        roicolor = case.PatientModel.RegionsOfInterest[RoiName].Color
        roimaterial = case.PatientModel.RegionsOfInterest[RoiName].RoiMaterial
        roitype = case.PatientModel.RegionsOfInterest[RoiName].Type

        droi = "DummyRoi"
        DummyRoi = UniqueRoi(droi, ss)
        NewRoi = UniqueRoi(RoiName, ss)

        # Increase the chosen ROI by margin and give it a dummy name
        with CompositeAction('Expand (RoiName)'):
            retval_0 = case.PatientModel.CreateRoi(Name=DummyRoi,
                                                   Color="Yellow",
                                                   Type="Organ",
                                                   TissueName=None,
                                                   RoiMaterial=None)
            retval_0.CreateMarginGeometry(Examination=examination, SourceRoiName=RoiName,
                                          MarginSettings={'Type': "Expand",
                                                          'Superior': margin,
                                                          'Inferior': margin,
                                                          'Anterior': margin,
                                                          'Posterior': margin,
                                                          'Right': margin,
                                                          'Left': margin})
        if self.vervangroi.IsChecked == True: 
            case.PatientModel.RegionsOfInterest[RoiName].CreateMarginGeometry(Examination = examination,
                                                                             SourceRoiName = DummyRoi,
                                                                             MarginSettings={ 'Type': "Contract",
                                                                                              'Superior': margin,
                                                                                              'Inferior': margin,
                                                                                              'Anterior': margin,
                                                                                              'Posterior': margin,
                                                                                              'Right': margin,
                                                                                              'Left': margin })

        else: 
            # Shrink the dummyroi by margin and give it its new name
            with CompositeAction('Contract (DummyRoi)'):
                retval_1 = case.PatientModel.CreateRoi(Name=NewRoi, 
                                                       Color=roicolor,
                                                       Type=roitype,
                                                       TissueName=None,
                                                       RoiMaterial=roimaterial)
                retval_1 = case.PatientModel.RegionsOfInterest[NewRoi].CreateMarginGeometry(Examination=examination,
                                                                                            SourceRoiName=DummyRoi,
                                                                                            MarginSettings={
                                                                                                'Type': "Contract",
                                                                                                'Superior': margin,
                                                                                                'Inferior': margin,
                                                                                                'Anterior': margin,
                                                                                                'Posterior': margin,
                                                                                                'Right': margin,
                                                                                                'Left': margin})

        # Remove the dummy roi
        case.PatientModel.RegionsOfInterest[DummyRoi].DeleteRoi()
        if self.vervangroi.IsChecked == False:
            MessageBox.Show('Finished.' + "\r\n" + "Rounded Roi is called: " + NewRoi, "Expand&ContractRoi",
                            MessageBoxButton.OK, MessageBoxImage.Information)
        self.SelectROI.SelectedIndex = -1
        return

    def ExtraClicked(self, sender, event):
        roi_name = str(self.SelectROI.SelectedItem)
        roi_name = str(self.SelectROI.SelectedItem)
        if roi_name in {"", 'None'}:
            # geen roi geselecteerd
            MessageBox.Show('First choose an ROI.', "Expand&ContractRoi", MessageBoxButton.OK,
                            MessageBoxImage.Information)
            return
        roi = ss.RoiGeometries[roi_name]
        if hasattr(roi.PrimaryShape, 'Contours'):
            msg = f"'{roi_name}' is in contourvorm..."
            print(msg)

            # controleer nu of de contour sagitaal is
            contours = roi.PrimaryShape.Contours
            if abs(contours[0][0].z - contours[0][1].z) > 1e-5:
                msg = f'Dit contour: {roi_name} is niet in transversale richting, converteren naar transversaal... '
                print(msg)
                roi.SetRepresentation(Representation='Triangle Mesh')
                roi.SetRepresentation(Representation='Contours')
            else:
                print("Deze contour is in transversale richting!")
        else:
            msg = f"'{roi_name}' is niet in contourvorm... Converteren naar contouren"
            print(msg)
            roi.SetRepresentation(Representation='Contours')

        # Voert nu verwijdering uit
        oude_contouren = roi.PrimaryShape.Contours  # moet de contouren opnieuw inlezen (trans)
        lengte = len(oude_contouren)
        print(f'Aantal coupes ={lengte}')
        if lengte <= 2:
            MessageBox.Show(
                f"'{roi_name}' aantal coupes ={lengte}: geen verwijdering nodig!"
            )

        verwijder = int(self.slValue2.Value)  # haal het nummer uit het juiste slider
        print(f"Houd een contour voor elke {verwijder} coupes!")

        mijn_coupes = []
        for j, slice in zip(range(lengte - 1), oude_contouren):
            if j % verwijder == 0:
                nieuwe_coupe = [{'x': p.x, 'y': p.y, 'z': p.z} for p in slice]
                mijn_coupes.append(nieuwe_coupe)
        # Laatste plak toevoegen
        laatste_coupe = oude_contouren[lengte - 1]
        nieuwe_coupe = [{'x': p.x, 'y': p.y, 'z': p.z} for p in laatste_coupe]
        mijn_coupes.append(nieuwe_coupe)

        ss.RoiGeometries[roi_name].PrimaryShape.Contours = mijn_coupes
        MessageBox.Show('Klaar')
        self.SelectROI.SelectedIndex = -1
        return

    def CloseClicked(self, sender, event):
        # Close window.
        sys.exit()


GetPlan()


class xaml():
    def __init__(self):
        self.xaml = """
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    ResizeMode="CanResizeWithGrip"
    Background="White"
    WindowStyle="ThreeDBorderWindow"
    AllowsTransparency="False"
    Title="ROI tools" Height="auto" Width="300" SizeToContent="Height">
    <Border Padding="2">
        <StackPanel>
            <GroupBox Header="ROI"
                      BorderThickness="2"
                      BorderBrush="LightBlue"
                      Margin="0,0"
                      Padding="2">
                <StackPanel Margin="8" Orientation="Horizontal">
                    <Label Content="Selecteer ROI:"/>
                    <ComboBox Name="SelectROI" Width="100"/>
                </StackPanel>
            </GroupBox>
            <GroupBox Header="Bewerking"
                      BorderThickness="2"
                      BorderBrush="LightBlue"
                      Margin="0,0"
                      Padding="2">
                <StackPanel Margin="2" Orientation="Vertical">
                   <CheckBox IsChecked="False"
                              FontWeight="Normal"
                              Margin="2"
                              HorizontalAlignment="Left"
                              x:Name="vervangroi">Vervang ROI</CheckBox>                  
                    <Label Content="Afrondings factor:"/>
                    <DockPanel VerticalAlignment="Center" Margin="10">
                        <TextBox Text="{Binding ElementName=slValue, Path=Value, UpdateSourceTrigger=PropertyChanged}" DockPanel.Dock="Right" TextAlignment="Right" Width="20" />
                        <Slider Maximum="2" Value="1" TickPlacement="BottomRight" TickFrequency="0.1" IsSnapToTickEnabled="True" Name="slValue" />
                    </DockPanel>
                    <Label Content="Deel totaal aantal coupes door:"/>
                    <DockPanel VerticalAlignment="Center" Margin="10">
                        <TextBox Text="{Binding ElementName=slValue2, Path=Value, UpdateSourceTrigger=PropertyChanged}" DockPanel.Dock="Right" TextAlignment="Right" Width="20" />
                        <Slider Maximum="10" Value="3" TickPlacement="BottomRight" TickFrequency="1" IsSnapToTickEnabled="True" Name="slValue2" />
                    </DockPanel>
                </StackPanel>
            </GroupBox>
            <UniformGrid Rows="1"
                         Columns="3">
                <Button Content="Afronden" Padding="5" Margin="2,5" Width="auto"
                            Click="ComputeClicked" Height="auto"/>
                <Button Content="Verw. coupes" Padding="5" Margin="2,5" Width="auto"
                            Click="ExtraClicked" Height="auto"/>
                <Button Content="Sluit" Padding="5" Margin="2,5" Width="auto" 
                            Click="CloseClicked" Height="auto"/>
            </UniformGrid>
        </StackPanel>
    </Border>
</Window> 
"""


if __name__ == '__main__':
    Application().Run(MyWindow())
