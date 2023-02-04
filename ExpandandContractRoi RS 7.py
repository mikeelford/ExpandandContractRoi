#------------------------------------------------------
# Name:        Expand&ContractRoi
# Purpose:     3D ROI rounding tool
# Author:      M. Elford
# Created:     16-11-2018 for RS vs 7.0
#------------------------------------------------------

import wpf
from System.Windows import *

def GetPlan():
    # ###########################################
    # ##  Code to get handles to plan data   ####
    # ###########################################
    global case, plan, exam, examination, ss
    try:
        case = get_current( 'Case' )
        examination = get_current( 'Examination' )
        ss = case.PatientModel.StructureSets[examination.Name]
    except:
        MessageBox.Show( 'A patient and plan must be loaded.', "Expand&ContractRoi", MessageBoxButton.OK, MessageBoxImage.Information)
        sys.exit()


def UniqueRoi(name, ss):
    for p in ss.RoiGeometries:
        if name == p.OfRoi.Name:
            name = f'{name}_1'
            name = UniqueRoi(name, ss)
    return name


class MyWindow(Window):
    def __init__(self):
        # Load xaml component.
        wpf.LoadComponent(self, 'ExpandandContractRoi.xaml')
        # Get the ROIs.
        roi_list = [roi.OfRoi.Name for roi in ss.RoiGeometries if roi.HasContours()]
        self.SelectROI.ItemsSource = roi_list


    def ComputeClicked(self, sender, event):
        # Get the ROI from the combobox.
        RoiName = self.SelectROI.SelectedItem

        if RoiName == "" or RoiName is None:
            # No ROI selected
            MessageBox.Show('First choose an ROI.',"Expand&ContractRoi", MessageBoxButton.OK, MessageBoxImage.Information) 
            return

        margin = self.slValue.Value

        roicolor = case.PatientModel.RegionsOfInterest[RoiName].Color
        roimaterial = case.PatientModel.RegionsOfInterest[RoiName].RoiMaterial
        #roitissue = case.PatientModel.RegionsOfInterest[RoiName].OrganData.TissueName
        roitype = case.PatientModel.RegionsOfInterest[RoiName].Type

        droi = "DummyRoi"
        DummyRoi = UniqueRoi(droi, ss)
        NewRoi = UniqueRoi(RoiName, ss)


        # Increase the chosen ROI by margin and give it a dummy name
        with CompositeAction('Expand (RoiName)'):
            retval_0 = case.PatientModel.CreateRoi(Name=DummyRoi, Color="Yellow", Type="Organ", TissueName=None, RoiMaterial=None)
            retval_0.CreateMarginGeometry(Examination=examination, SourceRoiName=RoiName, MarginSettings={ 'Type': "Expand", 'Superior': margin, 'Inferior': margin, 'Anterior': margin, 'Posterior': margin, 'Right': margin, 'Left': margin })
        # Shrink the dummyroi by margin and give it its new name
        with CompositeAction('Contract (DummyRoi)'):
            retval_1 = case.PatientModel.CreateRoi(Name=NewRoi, Color=roicolor, Type=roitype, TissueName=None, RoiMaterial=roimaterial)
            retval_1 = case.PatientModel.RegionsOfInterest[NewRoi].CreateMarginGeometry(Examination=examination, SourceRoiName=DummyRoi, MarginSettings={ 'Type': "Contract", 'Superior': margin, 'Inferior': margin, 'Anterior': margin, 'Posterior': margin, 'Right': margin, 'Left': margin })

        # Remove the dummy roi
        case.PatientModel.RegionsOfInterest[DummyRoi].DeleteRoi()
        MessageBox.Show('Finished.' + "\r\n" + "Rounded Roi is called: "  + NewRoi,"Expand&ContractRoi", MessageBoxButton.OK, MessageBoxImage.Information)
        self.SelectROI.SelectedIndex = -1

    def CloseClicked(self, sender, event): 
        # Close window.
        sys.exit()

# Run in RayStation.
from connect import * 
GetPlan()

if __name__ == '__main__':
    Application().Run(MyWindow())
