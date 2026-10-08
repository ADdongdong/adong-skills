// v2 is an explicit source-backed contract, never new fields on v1.
function validateCoDesign(intent) {
  const object = (v, name, keys) => {
    if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error(`${name} must be an object`);
    if (Object.keys(v).some(k => !keys.includes(k))) throw new Error(`${name} contains unknown fields`);
  };
  const text = (v, name) => { if (typeof v !== 'string' || !v.trim()) throw new Error(`${name} must be nonempty`); };
  const normalized = v => v.replace(/\s+/g, '').toLowerCase();
  object(intent,'outline_intent',['outline_intent_version','source','focus','regions','requirements','relationships','budget','target_width','target_height','min_font_size']);
  text(intent.source,'source'); text(intent.focus,'focus');
  const source = normalized(intent.source);
  const entries = (values, name, keys, check) => {
    if (!Array.isArray(values)) throw new Error(`${name} must be an array`);
    const ids = new Set();
    for (const v of values) {
      object(v,name,keys);
      if (typeof v.id !== 'string' || !/^[A-Za-z_][A-Za-z0-9_-]*$/.test(v.id) || ids.has(v.id)) throw new Error(`${name} requires unique stable IDs`);
      ids.add(v.id); text(v.source_quote,'source_quote');
      if (!source.includes(normalized(v.source_quote))) throw new Error('source_quote must be an excerpt of source');
      check(v);
    }
  };
  entries(intent.regions || [],'regions',['id','label','source_quote','purpose','suggestions','open','style_role'],r => {
    text(r.label,'region label');
    if (r.style_role != null && !['frame','foundation','planning','business'].includes(r.style_role)) throw new Error('invalid style_role');
    if (r.open !== undefined && (!Array.isArray(r.open) || r.open.some(v => !['layout','granularity','grouping','routing','style'].includes(v)))) throw new Error('invalid region open dimensions');
    if (r.suggestions !== undefined && (!r.suggestions || typeof r.suggestions !== 'object' || Array.isArray(r.suggestions))) throw new Error('suggestions must be an object');
  });
  const hard = new Map();
  const requirements = intent.requirements || [];
  entries(requirements,'requirements',['id','kind','target','related','value','strength','origin','source_quote'],r => {
    if (!['content','parent','edge','forbid_edge','highlight','grid_columns','grid_rows','direction','shared_boundary','relative_position','track_span'].includes(r.kind)) throw new Error('unsupported requirement kind');
    text(r.target,'target');
    if (['parent','edge','forbid_edge','shared_boundary','relative_position','track_span'].includes(r.kind)) text(r.related,'related');
    const strength = r.strength || 'hard', origin = r.origin || 'source';
    if (!['hard','soft'].includes(strength) || !['user','source','agent'].includes(origin)) throw new Error('invalid strength/origin');
    if (origin === 'agent' && strength === 'hard') throw new Error('agent suggestions cannot be hard');
    if (['grid_rows','grid_columns'].includes(r.kind) && (!Number.isInteger(r.value) || r.value < 1 || r.value > 100)) throw new Error('invalid grid dimension');
    if (r.kind === 'direction' && !['up','down','left','right'].includes(r.value)) throw new Error('invalid direction');
    if (r.kind === 'shared_boundary' && !['left','right','top','bottom'].includes(r.value)) throw new Error('invalid boundary');
    if (r.kind === 'relative_position' && !['left','right','above','below','same_row','same_column'].includes(r.value)) throw new Error('invalid position');
    if (r.kind === 'track_span') {
      const span = typeof r.value === 'string' && /^([1-9]\d{0,2}):([1-9]\d{0,2})$/.exec(r.value);
      if (!span || Number(span[1]) > Number(span[2]) || Number(span[2]) > 100) throw new Error('invalid track span');
    }
    if (r.kind === 'highlight' && !/^#[\da-f]{6}$/i.test(r.value)) throw new Error('invalid highlight color');
    if (strength === 'hard') {
      if (r.kind === 'content' && !source.includes(normalized(r.target))) throw new Error('hard content target must be literal source text');
      const key = JSON.stringify([r.kind,r.target,r.related,['shared_boundary','relative_position'].includes(r.kind) ? r.value : null]);
      if (hard.has(key) && hard.get(key) !== r.value) throw new Error('hard conflict');
      hard.set(key,r.value);
      if (r.kind === 'edge' && (intent.relationships === 'forbidden' || requirements.some(other => other.kind === 'forbid_edge' && other.strength !== 'soft' && other.target === r.target && other.related === r.related))) throw new Error('hard relationship conflict');
    }
  });
  if (intent.relationships !== undefined && !['unexpanded','required','forbidden'].includes(intent.relationships)) throw new Error('invalid relationship state');
  const bounds = (data, limits, name) => {
    for (const [key,[min,max]] of Object.entries(limits)) if (data[key] !== undefined && (!Number.isFinite(data[key]) || data[key] < min || data[key] > max || (key !== 'min_font_size' && !Number.isInteger(data[key])))) throw new Error(`${name}.${key} out of range`);
  };
  bounds(intent,{target_width:[320,10000],target_height:[240,10000],min_font_size:[1,100]},'intent');
  if (intent.budget !== undefined) {
    const limits = {model_repairs:[0,2],handoffs:[0,1],layout_candidates:[0,4],max_tokens:[1024,256000],seconds:[1,1800]};
    object(intent.budget,'budget',Object.keys(limits)); bounds(intent.budget,limits,'budget');
  }
  return intent;
}

module.exports = {validateCoDesign};
