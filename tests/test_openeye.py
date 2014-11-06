import simtk.unit as u
from simtk.openmm import app
import simtk.openmm as mm
import numpy as np
from mdtraj.testing import eq
from unittest import skipIf
from gaff2xml import utils
import os
import gaff2xml.openeye
import pandas as pd
import mdtraj as md

try:
    oechem = utils.import_("openeye.oechem")
    if not oechem.OEChemIsLicensed(): raise(ImportError("Need License for OEChem!"))
    oequacpac = utils.import_("openeye.oequacpac")
    if not oequacpac.OEQuacPacIsLicensed(): raise(ImportError("Need License for oequacpac!"))
    oeiupac = utils.import_("openeye.oeiupac")
    if not oeiupac.OEIUPACIsLicensed(): raise(ImportError("Need License for OEOmega!"))        
    oeomega = utils.import_("openeye.oeomega")
    if not oeomega.OEOmegaIsLicensed(): raise(ImportError("Need License for OEOmega!"))    
    HAVE_OE = True
except:
    HAVE_OE = False

@skipIf(not HAVE_OE, "Cannot test openeye module without OpenEye tools.")
def test_butanol_keepconfs():
    m0 = gaff2xml.openeye.iupac_to_oemol("butanol")
    m1 = gaff2xml.openeye.get_charges(m0, keep_confs=1)
    eq(m0.NumAtoms(), m1.NumAtoms())
    assert m1.NumConfs() == 1, "This OEMol was created to have a single conformation."
    assert m1.NumAtoms() == 15, "Butanol should have 15 atoms"


@skipIf(not HAVE_OE, "Cannot test openeye module without OpenEye tools.")
def test_butanol():
    m0 = gaff2xml.openeye.iupac_to_oemol("butanol")
    m1 = gaff2xml.openeye.get_charges(m0)
    eq(m0.NumAtoms(), m1.NumAtoms())
    assert m1.NumConfs() >= 2, "Butanol should have multiple conformers."
    assert m1.NumAtoms() == 15, "Butanol should have 15 atoms"
    
    all_data = {}
    for k, molecule in enumerate(m1.GetConfs()):
        names_to_charges, str_repr = gaff2xml.openeye.get_names_to_charges(molecule)
        all_data[k] = names_to_charges
        eq(sum(names_to_charges.values()), 0.0, decimal=7)  # Net charge should be zero
    
    # Build a table of charges indexed by conformer number and atom name
    all_data = pd.DataFrame(all_data)
    
    # The standard deviation along the conformer axis should be zero if all conformers have same charges
    eq(all_data.std(1).values, np.zeros(m1.NumAtoms()), decimal=7)
    
    with utils.enter_temp_directory():
        # Try saving to disk as mol2
        gaff2xml.openeye.molecule_to_mol2(m1, "out.mol2")
        # Make sure MDTraj can read the output
        t = md.load("out.mol2")
        # Make sure MDTraj can read the charges / topology info
        atoms, bonds = md.formats.mol2.mol2_to_dataframes("out.mol2")

        # Finally, make sure MDTraj and OpenEye report the same charges.
        names_to_charges, str_repr = gaff2xml.openeye.get_names_to_charges(m1)
        q = atoms.set_index("name").charge
        q0 = pd.Series(names_to_charges)
        delta = q - q0  # An object containing the charges, with atom names as indices
        eq(delta.values, np.zeros_like(delta.values), decimal=4)


@skipIf(not HAVE_OE, "Cannot test openeye module without OpenEye tools.")
def test_benzene():
    m0 = gaff2xml.openeye.iupac_to_oemol("benzene")
    m1 = gaff2xml.openeye.get_charges(m0)
    eq(m0.NumAtoms(), m1.NumAtoms())
    print(m1.NumConfs())
    assert m1.NumConfs() == 1, "Benezene should have 1 conformer"
    assert m1.NumAtoms() == 12, "Benezene should have 12 atoms"
    
    names_to_charges, str_repr = gaff2xml.openeye.get_names_to_charges(m1)
    eq(sum(names_to_charges.values()), 0.0, decimal=7)  # Net charge should be zero
    
    with utils.enter_temp_directory():
        # Try saving to disk as mol2
        gaff2xml.openeye.molecule_to_mol2(m1, "out.mol2")
        # Make sure MDTraj can read the output
        t = md.load("out.mol2")
        # Make sure MDTraj can read the charges / topology info
        atoms, bonds = md.formats.mol2.mol2_to_dataframes("out.mol2")

        # Finally, make sure MDTraj and OpenEye report the same charges.
        names_to_charges, str_repr = gaff2xml.openeye.get_names_to_charges(m1)
        q = atoms.set_index("name").charge
        q0 = pd.Series(names_to_charges)
        delta = q - q0  # An object containing the charges, with atom names as indices
        eq(delta.values, np.zeros_like(delta.values), decimal=4)


@skipIf(not HAVE_OE, "Cannot test openeye module without OpenEye tools.")
def test_link_in_utils():    
    m0 = gaff2xml.openeye.iupac_to_oemol("benzene")
    m1 = gaff2xml.openeye.get_charges(m0)
    with utils.enter_temp_directory():
        # This function was moved from utils to openeye, so check that the old link still works.
        utils.molecule_to_mol2(m1, "out.mol2")


@skipIf(not HAVE_OE, "Cannot test openeye module without OpenEye tools.")
def test_smiles():
    m0 = gaff2xml.openeye.smiles_to_oemol("CCCCO")
    charged0 = gaff2xml.openeye.get_charges(m0)

    m1 = gaff2xml.openeye.iupac_to_oemol("butanol")
    charged1 = gaff2xml.openeye.get_charges(m1)

    eq(charged0.NumAtoms(), charged1.NumAtoms())


@skipIf(not HAVE_OE, "Cannot test openeye module without OpenEye tools.")
def test_ffxml():
    with utils.enter_temp_directory():    
        m0 = gaff2xml.openeye.smiles_to_oemol("CCCCO")
        charged0 = gaff2xml.openeye.get_charges(m0)
        m1 = gaff2xml.openeye.smiles_to_oemol("ClC(Cl)(Cl)Cl")
        charged1 = gaff2xml.openeye.get_charges(m1)

        trajectories, ffxml = gaff2xml.openeye.oemols_to_ffxml([charged0, charged1])



@skipIf(not HAVE_OE, "Cannot test openeye module without OpenEye tools.")
def test_ffxml_simulation():
    """Test converting toluene and benzene smiles to oemol to ffxml to openmm simulation."""
    with utils.enter_temp_directory():    
        m0 = gaff2xml.openeye.smiles_to_oemol("Cc1ccccc1")
        charged0 = gaff2xml.openeye.get_charges(m0)
        m1 = gaff2xml.openeye.smiles_to_oemol("c1ccccc1")
        charged1 = gaff2xml.openeye.get_charges(m1)
        ligands = [charged0, charged1]
        n_atoms = [15,12]

        trajectories, ffxml = gaff2xml.openeye.oemols_to_ffxml(ligands)
        eq(len(trajectories),len(ligands))

        pdb_filename = utils.get_data_filename("chemicals/proteins/1vii.pdb")

        temperature = 300 * u.kelvin
        friction = 0.3 / u.picosecond
        timestep = 0.01 * u.femtosecond

        protein_traj = md.load(pdb_filename)
        protein_traj.center_coordinates()

        protein_top = protein_traj.top.to_openmm()
        protein_xyz = protein_traj.openmm_positions(0)

        for k, ligand in enumerate(ligands):
            ligand_traj = trajectories[k]
            ligand_traj.center_coordinates()
        
            eq(ligand_traj.n_atoms, n_atoms[k])
            eq(ligand_traj.n_frames, 1)

            #Move the pre-centered ligand sufficiently far away from the protein to avoid a clash.  
            min_atom_pair_distance = ((ligand_traj.xyz[0] ** 2.).sum(1) ** 0.5).max() + ((protein_traj.xyz[0] ** 2.).sum(1) ** 0.5).max() + 0.3
            ligand_traj.xyz += np.array([1.0, 0.0, 0.0]) * min_atom_pair_distance

            ligand_xyz = ligand_traj.openmm_positions(0)
            ligand_top = ligand_traj.top.to_openmm()

            ffxml.seek(0)
            forcefield = app.ForceField("amber10.xml", ffxml, "tip3p.xml")

            model = app.modeller.Modeller(protein_top, protein_xyz)
            model.add(ligand_top, ligand_xyz)
            model.addSolvent(forcefield, padding=0.4 * u.nanometer)

            system = forcefield.createSystem(model.topology, nonbondedMethod=app.PME, nonbondedCutoff=1.0 * u.nanometers, constraints=app.HAngles)

            integrator = mm.LangevinIntegrator(temperature, friction, timestep)

            simulation = app.Simulation(model.topology, system, integrator)
            simulation.context.setPositions(model.positions)
            print("running")
            simulation.step(1)
