"""Analytic free-fall and first-impact audits for the V66 guided drop."""
import math
import numpy as np

GRAVITY=9.81
DT=(.000625,.0003125,.00015625)
ADVANCE=(0.,.000625*5/16,.000625*10/16,.000625*15/16)


def start_state(advance):
    if advance not in ADVANCE:raise ValueError('unfrozen phase')
    return (0.,0.) if advance==0 else (-.5*GRAVITY*advance**2,-GRAVITY*advance)


def ballistic_position(position,velocity,dt,step):
    return position+velocity*step*dt-.5*GRAVITY*dt**2*step*(step+1)


def impact_prediction(clearance,advance,dt):
    if dt not in DT or not math.isfinite(clearance) or clearance<=0:
        raise ValueError('invalid step or initial clearance')
    q0,v0=start_state(advance)
    if clearance+q0<=0:raise ValueError('initial interference')
    # Stable positive root of the semi-implicit Euler free-fall polynomial.
    speed=-v0+.5*GRAVITY*dt
    root=2*(clearance+q0)/(math.sqrt(speed**2+2*GRAVITY*(clearance+q0))+speed)
    step=math.ceil(root/dt)
    while clearance+ballistic_position(q0,v0,dt,step)>0:step+=1
    while step>0 and clearance+ballistic_position(q0,v0,dt,step-1)<=0:step-=1
    continuous=math.sqrt(2*clearance/GRAVITY)-advance
    return {'solver_step':step,'solver_time_s':step*dt,
        'incoming_velocity_m_s':v0-GRAVITY*step*dt,
        'continuous_impact_time_s':continuous,
        'continuous_impact_velocity_m_s':-math.sqrt(2*GRAVITY*clearance),
        'initial_position_m':q0,'initial_velocity_m_s':v0}


def impact_audit(rows,clearance,advance,dt):
    prediction=impact_prediction(clearance,advance,dt)
    first=next((i for i,r in enumerate(rows) if r['normal_load_n']>1e-8),None)
    failures=[]
    if first is None:
        return {'passed':False,'failures':['missing_loaded_impact'],'prediction':prediction}
    selected=rows[first];q0,v0=start_state(advance)
    positions=[];velocities=[]
    for i,r in enumerate(rows[:first+1]):
        positions.append(abs(r['position_before_m']-ballistic_position(q0,v0,dt,i)))
        velocities.append(abs(r['velocity_before_m_s']-(v0-GRAVITY*i*dt)))
    position_error=max(positions);velocity_error=max(velocities)
    if first!=prediction['solver_step']:failures.append('onset_not_predicted_by_discrete_freefall')
    if position_error>1e-10 or velocity_error>1e-10:failures.append('ballistic_state_mismatch')
    time_error=selected['interval_start_s']-prediction['continuous_impact_time_s']
    incoming_error=selected['velocity_before_m_s']-prediction['continuous_impact_velocity_m_s']
    if abs(time_error)>dt+1e-9:failures.append('onset_outside_one_step')
    if abs(incoming_error)>GRAVITY*dt+1e-9:failures.append('incoming_velocity_outside_one_step')
    return {'passed':not failures,'failures':failures,'prediction':prediction,
        'loaded_step':first,'preimpact_samples_including_loaded_start':first+1,
        'maximum_freefall_position_error_m':position_error,'maximum_freefall_velocity_error_m_s':velocity_error,
        'observed_solver_time_s':selected['interval_start_s'],
        'observed_incoming_velocity_m_s':selected['velocity_before_m_s'],
        'continuous_onset_error_s':time_error,'continuous_incoming_velocity_error_m_s':incoming_error,
        'initial_energy_per_mass_m2_s2':.5*v0*v0+GRAVITY*(clearance+q0)}
