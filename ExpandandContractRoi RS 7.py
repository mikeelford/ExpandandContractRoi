#------------------------------------------------------
# Name:        Expand&ContractRoi
# Purpose:     3D ROI rounding tool
# Author:      M. Elford
# Created:     16-11-2018 for RS vs 7.0
#------------------------------------------------------

import wpf
from System.Windows import MessageBox
from System.Windows import Application, Window


def UniqueRoi(name, ss):
    for p in ss.RoiGeometries:
        if name == p.OfRoi.Name:
            name = name + '_1'
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
        #roi_list = [roi.OfRoi.Name for roi in ss.RoiGeometries]
        # Get the ROI from the combobox.
        RoiName = self.SelectROI.SelectedItem

        if RoiName == "" or RoiName == None:
            # No ROI selected
            MessageBox.Show('First choose a ROI.') 
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
        # Shrink the dummyroi by margin and give it its original name
        with CompositeAction('Contract (DummyRoi)'):
            retval_1 = case.PatientModel.CreateRoi(Name=NewRoi, Color=roicolor, Type=roitype, TissueName=None, RoiMaterial=roimaterial)
            retval_1 = case.PatientModel.RegionsOfInterest[NewRoi].CreateMarginGeometry(Examination=examination, SourceRoiName=DummyRoi, MarginSettings={ 'Type': "Contract", 'Superior': margin, 'Inferior': margin, 'Anterior': margin, 'Posterior': margin, 'Right': margin, 'Left': margin })

        # Remove the dummy roi
        case.PatientModel.RegionsOfInterest[DummyRoi].DeleteRoi()
        MessageBox.Show('Finished.' + "\r\n" + "Rounded Roi is called: "  + NewRoi)
        self.SelectROI.SelectedIndex = -1

    def CloseClicked(self, sender, event): 
        # Close window.
        sys.exit()

# Run in RayStation.
from connect import * 

try:
    examination = get_current('Examination')
    examname = examination.Name
    case = get_current('Case')
except:
    examination = get_current('Examination')
    examname = examination.Name
    case = get_current('Case')



ss = case.PatientModel.StructureSets[examination.Name]

if __name__ == '__main__':
    Application().Run(MyWindow())
