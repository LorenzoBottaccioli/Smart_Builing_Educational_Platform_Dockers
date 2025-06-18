// SurrogateObjectGrid.jsx
import React from 'react';

// Formatter functions for each surrogate object type
function formatMaterial(mat) {
  return `Material,
    ${mat.name},    !- Name
    ${mat.roughness},    !- Roughness
    ${mat.thickness},    !- Thickness {m}
    ${mat.conductivity},    !- Conductivity {W/m-K}
    ${mat.density},    !- Density {kg/m3}
    ${mat.specificHeat},    !- Specific Heat {J/kg-K}
    ${mat.thermalAbsorptance},    !- Thermal Absorptance
    ${mat.solarAbsorptance},    !- Solar Absorptance
    ${mat.visibleAbsorptance};    !- Visible Absorptance`;
}

function formatConstruction(c) {
  const layers = [c.outsideLayer, ...c.layers.slice(1).filter(l => l)];
  const layerLines = layers
    .map((layer, i) => `    ${layer},    !- Layer ${i + 1}`)
    .join('\n');
  return `Construction,
    ${c.name},    !- Name
${layerLines};`;
}

function formatFenestrationSurface(f) {
  const verts = f.vertices || [];
  const vertLines = verts
    .map((v, i) => `    ${v.x}, ${v.y}, ${v.z},    !- Vertex ${i + 1} X, Y, Z {m}`)
    .join('\n');
  return `FenestrationSurface:Detailed,
    ${f.name},    !- Name
    ${f.surfaceType},    !- Surface Type
    ${f.constructionName},    !- Construction Name
    ${f.buildingSurfaceName},    !- Building Surface Name
    ${f.outsideBoundaryConditionObject},    !- Outside Boundary Condition Object
    ${f.viewFactorToGround},    !- View Factor to Ground
    ${f.frameAndDividerName || ''},    !- Frame and Divider Name
    ${f.multiplier},    !- Multiplier
    ${verts.length},    !- Number of Vertices
${vertLines};`;
}

function formatZoneVentilation(v) {
  return `ZoneVentilation:DesignFlowRate,
    ${v.name},    !- Name
    ${v.zone_name},    !- Zone or ZoneList Name
    ${v.schedule_name},    !- Schedule Name
    ${v.design_flow_rate_calculation_method},    !- Design Flow Rate Calculation Method
    ${v.design_flow_rate},    !- Design Flow Rate {m3/s}
    ${v.flow_per_zone_floor_area},    !- Flow Rate per Zone Floor Area {m3/s-m2}
    ${v.flow_rate_per_person},    !- Flow Rate per Person {m3/s-person}
    ${v.air_changes_per_hour},    !- Air Changes per Hour {1/hr}
    ${v.ventilation_type},    !- Ventilation Type
    ${v.fan_pressure_rise},    !- Fan Pressure Rise {Pa}
    ${v.fan_total_efficiency},    !- Fan Total Efficiency
    ${v.constant_term_coefficient},    !- Constant Term Coefficient
    ${v.temperature_term_coefficient},    !- Temperature Term Coefficient
    ${v.velocity_term_coefficient},    !- Velocity Term Coefficient
    ${v.velocity_squared_term_coefficient},    !- Velocity Squared Term Coefficient
    ${v.minimum_indoor_temperature},    !- Minimum Indoor Temperature {C}
    ${v.minimum_indoor_temp_schedule},    !- Minimum Indoor Temperature Schedule Name
    ${v.maximum_indoor_temperature},    !- Maximum Indoor Temperature {C}
    ${v.maximum_indoor_temp_schedule},    !- Maximum Indoor Temperature Schedule Name
    ${v.delta_temperature},    !- Delta Temperature {deltaC}
    ${v.delta_temp_schedule},    !- Delta Temperature Schedule Name
    ${v.minimum_outdoor_temperature},    !- Minimum Outdoor Temperature {C}
    ${v.minimum_outdoor_temp_schedule},    !- Minimum Outdoor Temperature Schedule Name
    ${v.maximum_outdoor_temperature},    !- Maximum Outdoor Temperature {C}
    ${v.maximum_outdoor_temp_schedule},    !- Maximum Outdoor Temperature Schedule Name
    ${v.maximum_wind_speed};    !- Maximum Wind Speed {m/s}`;
}

function formatLights(l) {
  return `Lights,
    ${l.name},    !- Name
    ${l.zone_or_space_name},    !- Zone or ZoneList or Space or SpaceList Name
    ${l.schedule_name},    !- Schedule Name
    ${l.design_level_calculation_method},    !- Design Level Calculation Method
    ${l.lighting_level},    !- Lighting Level {W}
    ${l.watts_per_zone_floor_area},    !- Watts per Zone Floor Area {W/m2}
    ${l.watts_per_person},    !- Watts per Person {W/person}
    ${l.return_air_fraction},    !- Return Air Fraction
    ${l.fraction_radiant},    !- Fraction Radiant
    ${l.fraction_visible},    !- Fraction Visible
    ${l.fraction_replaceable},    !- Fraction Replaceable
    ${l.end_use_subcategory};    !- End-Use Subcategory`;
}

function formatWindowShading(s) {
  const surfaces = [];
  for (let i = 1; i <= 10; i++) {
    const key = `fenestration_surface_${i}_name`;
    if (s[key]) surfaces.push(s[key]);
  }
  const surfLines = surfaces
    .map((name, idx) => `    ${name},    !- Fenestration Surface ${idx + 1} Name`)
    .join('\n');
  return `WindowShadingControl,
    ${s.name},    !- Name
    ${s.zone_name},    !- Zone Name
    ${s.shading_control_sequence},    !- Shading Control Sequence Number
    ${s.shading_type},    !- Shading Type
    ${s.construction_with_shading_name},    !- Construction with Shading Name
    ${s.shading_control_type},    !- Shading Control Type
    ${s.schedule_name},    !- Schedule Name
    ${s.setpoint},    !- Setpoint {W/m2, W or deg C}
    ${s.shading_control_is_scheduled},    !- Shading Control Is Scheduled
    ${s.glare_control_is_active},    !- Glare Control Is Active
    ${s.shading_device_material_name},    !- Shading Device Material Name
    ${s.slat_angle_control_type},    !- Type of Slat Angle Control for Blinds
    ${s.slat_angle_schedule_name},    !- Slat Angle Schedule Name
    ${s.setpoint_2},    !- Setpoint 2 {W/m2 or deg C}
    ${s.daylighting_control_object_name},    !- Daylighting Control Object Name
    ${s.multiple_surface_control_type},    !- Multiple Surface Control Type
${surfLines};`;
}

// Map type key to appropriate formatter
const formatters = {
  materials: formatMaterial,
  constructions: formatConstruction,
  fenestration_surfaces: formatFenestrationSurface,
  zone_ventilations: formatZoneVentilation,
  lights: formatLights,
  window_shading_controls: formatWindowShading
};

/**
 * SurrogateObjectGrid
 * Props:
 *  - objects: array of JSON objects from the backend
 *  - type: one of 'materials', 'constructions', etc.
 */
export default function SurrogateObjectGrid({ objects = [], type }) {
  const formatter = formatters[type];
  return (
    <div style={{ border: '1px solid #ccc', padding: '10px' }}>
      {objects.length > 0 ? (
        objects.map(obj => (
          <pre
            key={obj.id}
            style={{ whiteSpace: 'pre-wrap', marginBottom: '1rem' }}
          >
            {formatter(obj)}
          </pre>
        ))
      ) : (
        <p>No objects of type <strong>{type}</strong></p>
      )}
    </div>
  );
}
