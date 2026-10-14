"""Generate the raw-data serialization-cost figure as an embedded-font vector."""
import argparse
import json
import tempfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.text import Text
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


def truetype_font(source, directory):
    """Keep the supplied face; convert CFF outlines for Type42 embedding only.

    The installed TeX Gyre Termes is CFF OTF. Cubic-to-quadratic conversion
    uses 0.1 units per 1000 UPEM before integer coordinate rounding. Its cmap,
    advance widths, names (including copyright), and layout tables stay intact.
    No converted font is installed or distributed as an artifact file.
    """
    with TTFont(source, recalcTimestamp=False) as font:
        if font['OS/2'].fsType & 0x0302:
            raise ValueError('Font does not permit the required outline subsetting')
        if 'glyf' in font:
            return source
        if 'CFF ' not in font:
            raise ValueError('Expected TrueType or ordinary CFF font outlines')
        order = font.getGlyphOrder()
        cmap = font.getBestCmap().copy()
        metrics = font['hmtx'].metrics.copy()
        names = font['name'].compile(font)
        upem = font['head'].unitsPerEm
        glyph_set = font.getGlyphSet()
        glyphs = {}
        for name in order:
            pen = TTGlyphPen(glyph_set)
            glyph_set[name].draw(Cu2QuPen(pen, upem/10000, reverse_direction=True))
            glyphs[name] = pen.glyph()
        post_values = {key:getattr(font['post'], key) for key in (
            'italicAngle', 'underlinePosition', 'underlineThickness', 'isFixedPitch',
            'minMemType42', 'maxMemType42', 'minMemType1', 'maxMemType1')}
        del font['CFF ']
        font.sfntVersion = '\x00\x01\x00\x00'
        font['head'].glyphDataFormat = 0
        builder = FontBuilder(font=font)
        builder.isTTF = True
        builder.setupGlyf(glyphs)
        builder.setupMaxp()
        builder.setupPost(**post_values)
        target = Path(directory)/'matching-outlines.ttf'
        font.save(target)
    with TTFont(target) as converted:
        if (converted.getGlyphOrder() != order or converted.getBestCmap() != cmap
                or converted['hmtx'].metrics != metrics
                or converted['name'].compile(converted) != names
                or converted['head'].unitsPerEm != upem or 'glyf' not in converted):
            raise RuntimeError('TrueType conversion changed font identity or metrics')
    return target


def draw(args, configs, stats, font_path):
    admitted=[c for c in configs if c['status']=='identified']
    font_manager.fontManager.addfont(str(font_path))
    family=font_manager.FontProperties(fname=str(font_path)).get_name()
    plt.rcParams.update({'font.family':family,'font.size':9,'pdf.fonttype':42,'ps.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(7.0,2.7),gridspec_kw={'width_ratios':[1.55,1]})
    colors={'whole':'#777777','prefix':'#1c7387','bit':'#bb592b'}
    for method in ('whole','prefix','bit'):
        axes[0].plot(range(len(admitted)),[c['depths'][method] for c in admitted],marker='o' if method=='bit' else '.',label=method,color=colors[method],linewidth=1)
    axes[0].set(xlabel='Admitted configuration (catalog order)',ylabel='Worst-case symbol depth',ylim=(0,13))
    axes[0].legend(frameon=False,ncol=3,loc='upper left',fontsize=8); axes[0].grid(axis='y',alpha=.2)
    for index,mode in enumerate(('normal','optimized')):
        axes[1].bar([x+(.18 if index else -.18) for x in range(3)],
                    [stats[mode]['arms'][m]['harness_wall_median_seconds']*1000 for m in ('whole','prefix','bit')],width=.32,label='Python '+('normal' if index==0 else '-O'),color=('#90b8be' if index==0 else '#c9b197'))
    axes[1].set(xticks=range(3),xticklabels=['whole','prefix','bit'],ylabel='Median full process wall time (ms)')
    axes[1].set_ylim(0,max(stats[mode]['arms'][m]['harness_wall_median_seconds']*1000 for mode in ('normal','optimized') for m in ('whole','prefix','bit'))*1.38)
    axes[1].legend(frameon=False,fontsize=8); axes[1].grid(axis='y',alpha=.2)
    # Bind every label to this file, not a same-family CFF font in a local cache.
    fig.canvas.draw()
    for text in fig.findobj(Text):
        properties = text.get_fontproperties().copy()
        properties.set_file(str(font_path))
        text.set_fontproperties(properties)
    fig.tight_layout()
    for suffix in ('.pdf','.svg'):
        fig.savefig(args.out.with_suffix(suffix),metadata={'Creator':'Matplotlib '+matplotlib.__version__} if suffix=='.pdf' else None)
    print(json.dumps(dict(matplotlib=matplotlib.__version__,font_family=family,font_file=str(args.font),pdf_fonttype=42,admitted_configurations=len(admitted),verified_input=str(args.verified),output=str(args.out)),sort_keys=True))
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',type=Path,required=True); ap.add_argument('--verified',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--font',type=Path)
    args=ap.parse_args()
    configs=json.loads(args.data.read_text(encoding='utf-8')); stats=json.loads(args.verified.read_text(encoding='utf-8'))
    source = args.font or Path(font_manager.findfont(font_manager.FontProperties(family='serif')))
    with tempfile.TemporaryDirectory(prefix='serialization-font-') as directory:
        try:
            draw(args, configs, stats, truetype_font(source, directory))
        finally:
            # Matplotlib 3.10.7 caches open FreeType handles. Release them before
            # removing the temporary font on Windows; do not suppress cleanup.
            font_manager._get_font.cache_clear()


if __name__=='__main__': main()
