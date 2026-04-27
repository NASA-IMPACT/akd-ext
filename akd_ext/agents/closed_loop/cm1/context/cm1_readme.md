Directory structure:
└── config_files/
    ├── README.md
    ├── namelist.input
    ├── cpm_RadConvEquil/
    │   ├── README
    │   ├── input_sounding
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── dns_RayleighBenard/
    │   ├── README
    │   └── namelist.input
    ├── hurricane_3d_cpm/
    │   ├── README
    │   ├── input_sounding
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── hurricane_axisymmetric/
    │   ├── README
    │   ├── input_sounding
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── hurricane_les_within_mm/
    │   ├── README
    │   ├── input_sounding
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_ConvBoundLayer/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_ConvPBL_moisture/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_HurrBoundLayer/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_HurrCoast/
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_ib_windtunnel/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_ShallowCu/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_ShallowCuLand/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_ShallowCuPrecip/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_ShearBoundLayer/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_StableBoundLayer/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_StratoCuDrizzle/
    │   ├── README
    │   ├── input_grid_z
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── les_StratoCuNoPrecip/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── nh_mountain_waves/
    │   ├── README
    │   └── namelist.input
    ├── scm_HurrBoundLayer/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── scm_HurrBoundLayer_tqnudge/
    │   ├── README
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── sea_breeze/
    │   ├── README
    │   ├── input_sounding
    │   ├── LANDUSE.TBL
    │   └── namelist.input
    ├── squall_line/
    │   ├── README
    │   └── namelist.input
    └── supercell/
        ├── README
        └── namelist.input

================================================
FILE: run/config_files/README.md
================================================

 For more information on each case, please see the README file in each
 subdirectory.



 Acronyms:

 CPM  -  Convection-Permitting Model

 DNS  -  Direct Numerical Simulation

 IB  -  Immersed Boundaries

 LES  -  Large-Eddy Simulation

 MM  -  Mesoscale Model

 NH  - Nonhydrostatic

 SCM  -  Single-Column Model



================================================
FILE: run/config_files/namelist.input
================================================

 &param0
 nx           =      60,
 ny           =      60,
 nz           =      40,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 outunits     =       1,
 /

 &param1
 dx     =  2000.0,
 dy     =  2000.0,
 dz     =   500.0,
 dtl    =   7.500,
 timax  =  7200.0,
 run_time =  -999.9,
 tapfrq =   900.0,
 rstfrq = -3600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  0,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  1,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  0,
 betaplane =  0,
 lspgrad   =  0,
 eqtset    =  2,
 idiss     =  1,
 efall     =  0,
 rterm     =  0,
 wbc       =  2,
 ebc       =  2,
 sbc       =  2,
 nbc       =  2,
 bbc       =  1,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  5,
 iwnd      =  2,
 itern     =  0,
 iinit     =  1,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  1,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 15000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    250.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      0,
 sfcmodel   =      0,
 oceanmodel =      0,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = 18000.0,
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 1,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 0,
 output_sfcparams = 0,
 output_sfcdiags  = 0,
 output_psfc      = 0,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 1,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/cpm_RadConvEquil/README
================================================


  Cloud Permitting Model (CPM) simulation of Radiative Convective Equilibrium
  (RCE) following Bretherton et al. (2005, JAS, pg 4273).


  NOTE: no diurnal cycle.  (Solar constant is fixed at 650.83 W/m2)



================================================
FILE: run/config_files/cpm_RadConvEquil/input_sounding
================================================
     1014.80       298.6949       18.63960
    124.0000       299.6500       18.58188    0.00    0.00
    810.0000       301.6888       15.30626    0.00    0.00
   1541.0000       304.5541       11.98349    0.00    0.00
   3178.0000       312.2750        6.76311    0.00    0.00
   4437.0000       317.8749        4.15019    0.00    0.00
   5887.0000       324.8602        2.42535    0.00    0.00
   7596.0000       332.5846        1.11535    0.00    0.00
   9690.0000       339.6121        0.32924    0.00    0.00
  10949.0000       342.8986        0.13712    0.00    0.00
  12418.0000       346.4510        0.04282    0.00    0.00
  14203.0000       353.9290        0.01063    0.00    0.00
  16590.0000       383.2672        0.00532    0.00    0.00
  20726.0000       494.1519        0.04066    0.00    0.00
  40000.0000      1010.8810        0.00000    0.00    0.00



================================================
FILE: run/config_files/cpm_RadConvEquil/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/cpm_RadConvEquil/namelist.input
================================================

 &param0
 nx           =     192,
 ny           =     192,
 nz           =      65,
 ppnode       =     128,
 timeformat   =       4,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =  3000.0,
 dy     =  3000.0,
 dz     =   500.0,
 dtl    =  15.000,
 timax  = 8640000.0,
 run_time =  -999.9,
 tapfrq =   86400.0,
 rstfrq =  864000.0,
 statfrq =   3600.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  2,
 testcase  =  8,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  2,
 sgsmodel  =  0,
 tconfig   =  2,
 bcturbs   =  2,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  2,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  0,
 betaplane =  0,
 lspgrad   =  0,
 eqtset    =  2,
 idiss     =  1,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  7,
 iwnd      =  0,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.0000,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 20000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        2,
 dtrad   =    300.0,
 ctrlat  =     0.00,
 ctrlon  =     0.00,
 year    =     2009,
 month   =        7,
 day     =        1,
 hour    =       00,
 minute  =       00,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 301.00,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      = 28000.0,
 str_bot   =     0.0,
 str_top   =  5500.0,
 dz_bot    =    50.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 1,
 output_cape      = 1,
 output_cin       = 1,
 output_lcl       = 1,
 output_lfc       = 1,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 0,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =     3600.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/dns_RayleighBenard/README
================================================

  Rayleigh-Benard convection, following Moeng and Rotunno (1990, JAS, pg 1149),
  using Direct Numerical Simulation (DNS).



================================================
FILE: run/config_files/dns_RayleighBenard/namelist.input
================================================

 &param0
 nx           =      96,
 ny           =      96,
 nz           =     100,
 ppnode       =     128,
 timeformat   =       1,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    60.0,
 dy     =    60.0,
 dz     =    10.0,
 dtl    =     1.0,
 timax  =  6000.0,
 run_time =  -999.9,
 tapfrq =  1000.0,
 rstfrq = -3600.0,
 statfrq =   10.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  3,
 testcase  =  0,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  0,
 sgsmodel  =  0,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  0,
 irdamp    =  0,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  1,
 iautoc    =  1,
 icor      =  0,
 lspgrad   =  0,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  2,
 tbc       =  2,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  8,
 iwnd      =  0,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 15000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    250.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      0,
 sfcmodel   =      0,
 oceanmodel =      0,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = 18000.0,
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 296.9419,
 ptc_bot   = 300.0,
 viscosity = 16.23,
 pr_num    = 1.00,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 1,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 0,
 output_sfcparams = 0,
 output_sfcdiags  = 0,
 output_psfc      = 0,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 1,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =      100.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/hurricane_3d_cpm/README
================================================

  Idealized hurricane simulation, 3D, convection permitting model (CPM)
  using parameterized turbulence (aka, a "mesoscale model" type of configuration).

  Based mostly on Bryan (2012, MWR, pg 1125).

  This case uses the "Moist Tropical" sounding from Dunion (2011, J. Climate,
  pg 893), by default, with a sea-surface temperature of 28 C.



================================================
FILE: run/config_files/hurricane_3d_cpm/input_sounding
================================================
     1014.80       298.6949       18.63960
    124.0000       299.6500       18.58188    0.00    0.00
    810.0000       301.6888       15.30626    0.00    0.00
   1541.0000       304.5541       11.98349    0.00    0.00
   3178.0000       312.2750        6.76311    0.00    0.00
   4437.0000       317.8749        4.15019    0.00    0.00
   5887.0000       324.8602        2.42535    0.00    0.00
   7596.0000       332.5846        1.11535    0.00    0.00
   9690.0000       339.6121        0.32924    0.00    0.00
  10949.0000       342.8986        0.13712    0.00    0.00
  12418.0000       346.4510        0.04282    0.00    0.00
  14203.0000       353.9290        0.01063    0.00    0.00
  16590.0000       383.2672        0.00532    0.00    0.00
  20726.0000       494.1519        0.04066    0.00    0.00
  40000.0000      1010.8810        0.00000    0.00    0.00



================================================
FILE: run/config_files/hurricane_3d_cpm/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/hurricane_3d_cpm/namelist.input
================================================

 &param0
 nx           =     384,
 ny           =     384,
 nz           =      59,
 ppnode       =     128,
 timeformat   =       4,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =  4000.0,
 dy     =  4000.0,
 dz     =   500.0,
 dtl    =  10.000,
 timax  =  691200.0,
 run_time =  -999.9,
 tapfrq =   86400.0,
 rstfrq =  345600.0,
 statfrq =   3600.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  2,
 testcase  =  0,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  2,
 sgsmodel  =  0,
 tconfig   =  2,
 bcturbs   =  1,
 horizturb =  1,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  1,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  1,
 betaplane =  0,
 lspgrad   =  1,
 eqtset    =  2,
 idiss     =  1,
 efall     =  0,
 rterm     =  1,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  7,
 iwnd      =  0,
 itern     =  0,
 iinit     =  7,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 20000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 301.15,
 tmn0       = 299.15,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      1,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      1,
 dx_inner  =    4000.0,
 dx_outer  =   16000.0,
 nos_x_len =  560000.0,
 tot_x_len = 3000000.0,
 /

 &param5
 stretch_y =      1,
 dy_inner  =    4000.0,
 dy_outer  =   16000.0,
 nos_y_len =  560000.0,
 tot_y_len = 3000000.0,
 /

 &param6
 stretch_z =  1,
 ztop      = 25000.0,
 str_bot   =     0.0,
 str_top   =  5500.0,
 dz_bot    =    50.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 0,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .true.,
 azimavgfrq       =     3600.0,
 rlen             =   500000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/hurricane_axisymmetric/README
================================================

  Idealized hurricane simulation, axisymmetric, using parameterized turbulence
  (i.e., a "mesoscale model" type of configuration).

  Based mostly on Bryan (2012, MWR, pg 1125).

  This case uses the "Moist Tropical" sounding from Dunion (2011, J. Climate,
  pg 893), by default, with a sea-surface temperature of 28 C.



================================================
FILE: run/config_files/hurricane_axisymmetric/input_sounding
================================================
     1014.80       298.6949       18.63960
    124.0000       299.6500       18.58188    0.00    0.00
    810.0000       301.6888       15.30626    0.00    0.00
   1541.0000       304.5541       11.98349    0.00    0.00
   3178.0000       312.2750        6.76311    0.00    0.00
   4437.0000       317.8749        4.15019    0.00    0.00
   5887.0000       324.8602        2.42535    0.00    0.00
   7596.0000       332.5846        1.11535    0.00    0.00
   9690.0000       339.6121        0.32924    0.00    0.00
  10949.0000       342.8986        0.13712    0.00    0.00
  12418.0000       346.4510        0.04282    0.00    0.00
  14203.0000       353.9290        0.01063    0.00    0.00
  16590.0000       383.2672        0.00532    0.00    0.00
  20726.0000       494.1519        0.04066    0.00    0.00
  40000.0000      1010.8810        0.00000    0.00    0.00



================================================
FILE: run/config_files/hurricane_axisymmetric/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/hurricane_axisymmetric/namelist.input
================================================

 &param0
 nx           =     192,
 ny           =       1,
 nz           =      59,
 ppnode       =     128,
 timeformat   =       4,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =  4000.0,
 dy     =  4000.0,
 dz     =   500.0,
 dtl    =  10.000,
 timax  =  691200.0,
 run_time =  -999.9,
 tapfrq =    3600.0,
 rstfrq =  345600.0,
 statfrq =   3600.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  2,
 testcase  =  0,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  2,
 sgsmodel  =  0,
 tconfig   =  2,
 bcturbs   =  1,
 horizturb =  1,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  1,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  1,
 betaplane =  0,
 lspgrad   =  0,
 eqtset    =  2,
 idiss     =  1,
 efall     =  0,
 rterm     =  1,
 wbc       =  3,
 ebc       =  3,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  7,
 iwnd      =  0,
 itern     =  0,
 iinit     =  7,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  1,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 20000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 301.15,
 tmn0       = 299.15,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      1,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      2,
 dx_inner  =    4000.0,
 dx_outer  =   16000.0,
 nos_x_len =  280000.0,
 tot_x_len = 1500000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      = 25000.0,
 str_bot   =     0.0,
 str_top   =  5500.0,
 dz_bot    =    50.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 1,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/hurricane_les_within_mm/README
================================================

  Idealized hurricane simulation, 3D, using the LES-within-mesoscale-model
  configuration (ie, large-eddy-simulation without a PBL parameterization
  near center of domain; mesoscale modeling with a PBL parameterization
  at larger radii).

  This case uses the "Moist Tropical" sounding from Dunion (2011, J. Climate,
  pg 893), by default, with a sea-surface temperature of 28 C.



================================================
FILE: run/config_files/hurricane_les_within_mm/input_sounding
================================================
     1014.80       298.6949       18.63960
    124.0000       299.6500       18.58188    0.00    0.00
    810.0000       301.6888       15.30626    0.00    0.00
   1541.0000       304.5541       11.98349    0.00    0.00
   3178.0000       312.2750        6.76311    0.00    0.00
   4437.0000       317.8749        4.15019    0.00    0.00
   5887.0000       324.8602        2.42535    0.00    0.00
   7596.0000       332.5846        1.11535    0.00    0.00
   9690.0000       339.6121        0.32924    0.00    0.00
  10949.0000       342.8986        0.13712    0.00    0.00
  12418.0000       346.4510        0.04282    0.00    0.00
  14203.0000       353.9290        0.01063    0.00    0.00
  16590.0000       383.2672        0.00532    0.00    0.00
  20726.0000       494.1519        0.04066    0.00    0.00
  40000.0000      1010.8810        0.00000    0.00    0.00



================================================
FILE: run/config_files/hurricane_les_within_mm/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/hurricane_les_within_mm/namelist.input
================================================

 &param0
 nx           =    1144,
 ny           =    1144,
 nz           =     106,
 ppnode       =     128,
 timeformat   =       3,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =   250.0,
 dy     =   250.0,
 dz     =   250.0,
 dtl    =   5.000,
 timax  =  691200.0,
 run_time =  -999.9,
 tapfrq =   10800.0,
 rstfrq =   86400.0,
 statfrq =    300.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  4,
 testcase  =  0,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  2,
 sgsmodel  =  4,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  1,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  1,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  1,
 betaplane =  0,
 lspgrad   =  1,
 eqtset    =  1,
 idiss     =  1,
 efall     =  0,
 rterm     =  1,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  7,
 iwnd      =  0,
 itern     =  0,
 iinit     =  7,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 20000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 301.15,
 tmn0       = 299.15,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      1,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       2,
 /

 &param4
 stretch_x =      1,
 dx_inner  =     250.0,
 dx_outer  =   16000.0,
 nos_x_len =  200000.0,
 tot_x_len = 2995000.0,
 /

 &param5
 stretch_y =      1,
 dy_inner  =     250.0,
 dy_outer  =   16000.0,
 nos_y_len =  200000.0,
 tot_y_len = 2995000.0,
 /

 &param6
 stretch_z =  1,
 ztop      = 25000.0,
 str_bot   =     0.0,
 str_top   =  3500.0,
 dz_bot    =   100.0,
 dz_top    =   250.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 0,
 output_sps       = 0,
 output_srs       = 0,
 output_sgs       = 0,
 output_sus       = 0,
 output_shs       = 0,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 0,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .true.,
 azimavgfrq       =     3600.0,
 rlen             =   500000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .true.,
 do_recycle_s        =  .true.,
 do_recycle_e        =  .true.,
 do_recycle_n        =  .true.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  6000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_ConvBoundLayer/README
================================================

  Convective boundary layer (CBL) using Large Eddy Simulation (LES)
  following Sullivan and Patton (2011, JAS, pg 2395).



================================================
FILE: run/config_files/les_ConvBoundLayer/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_ConvBoundLayer/namelist.input
================================================

 &param0
 nx           =     128,
 ny           =     128,
 nz           =     128,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    40.0,
 dy     =    40.0,
 dz     =    16.0,
 dtl    =   1.500,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq = 10800.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  1,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  1,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 14,
 iwnd      =  6,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 1.000e-4,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  2000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      5,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    1.0,
 lu0        =      3,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx =   0.24,
 cnst_lhflx =   0.00,
 set_znt    =      1,
 cnst_znt   =   0.10,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      =  3000.0,
 str_bot   =  1536.0,
 str_top   =  3000.0,
 dz_bot    =   16.0,
 dz_top    =   75.5,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_ConvPBL_moisture/README
================================================

  Convective boundary layer with moisture (but no clouds) using
  Large Eddy Simulation (LES) following NCAR LES intercomparison case.
  Based on observations from Southeast Atmosphere Study (SAS).



================================================
FILE: run/config_files/les_ConvPBL_moisture/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_ConvPBL_moisture/namelist.input
================================================

 &param0
 nx           =     512,
 ny           =     512,
 nz           =     200,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    15.0,
 dy     =    15.0,
 dz     =    15.0,
 dtl    =   5.000,
 timax  = 46800.0,
 run_time =  -999.9,
 tapfrq =   300.0,
 rstfrq = 21600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  = 11,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  4,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  0,
 irdamp    =  0,
 hrdamp    =  0,
 psolver   =  7,
 ptype     =  0,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  2,
 eqtset    =  1,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 19,
 iwnd      =  6,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.000,
 fcor    = 7.90038-5,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  2500.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      5,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    1.0,
 lu0        =      3,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx =   0.24,
 cnst_lhflx =   0.00,
 set_znt    =      1,
 cnst_znt   =   0.70,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 7200.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      =  3000.0,
 str_bot   =  1536.0,
 str_top   =  3000.0,
 dz_bot    =   16.0,
 dz_top    =   75.5,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 0,
 output_sws       = 0,
 output_svs       = 0,
 output_sps       = 0,
 output_srs       = 0,
 output_sgs       = 0,
 output_sus       = 0,
 output_shs       = 0,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 0,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 1,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 0,
 output_kh        = 0,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 0,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 0,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 0,
 output_w         = 1,
 output_winterp   = 0,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =      300.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_HurrBoundLayer/README
================================================

  Simple hurricane boundary layer (HBL) using Large Eddy Simulation (LES)
  following Bryan et al (2017, BLM, pg 475).



================================================
FILE: run/config_files/les_HurrBoundLayer/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_HurrBoundLayer/namelist.input
================================================

 &param0
 nx           =     128,
 ny           =     128,
 nz           =     128,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    40.0,
 dy     =    40.0,
 dz     =    20.0,
 dtl    =   1.000,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq = 10800.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  6,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  3,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  8,
 iwnd      =  8,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  2000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 301.15,
 tmn0       = 299.15,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx =   0.10,
 cnst_lhflx =   0.00,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      =  2980.0,
 str_bot   =  2000.0,
 str_top   =  2980.0,
 dz_bot    =   20.0,
 dz_top    =   50.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =     .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_HurrCoast/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_HurrCoast/namelist.input
================================================

 &param0
 nx           =     600,
 ny           =     200,
 nz           =     100,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    20.0,
 dy     =    20.0,
 dz     =    20.0,
 dtl    =   0.500,
 timax  = 14400.0,
 run_time =  -999.9,
 tapfrq =   300.0,
 rstfrq =  7200.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  = 15,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  0,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  0,
 irdamp    =  2,
 hrdamp    =  0,
 psolver   =  2,
 ptype     =  0,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 betaplane =  0,
 lspgrad   =  3,
 eqtset    =  1,
 idiss     =  1,
 efall     =  0,
 rterm     =  0,
 wbc       =  2,
 ebc       =  2,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  2,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  8,
 iwnd      =  8,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  1500.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =     -1.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =    100.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      0,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      4,
 tsk0       = 301.15,
 tmn0       = 299.15,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.10,
 cnst_lhflx =   0.00,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      =  2980.0,
 str_bot   =  2000.0,
 str_top   =  2980.0,
 dz_bot    =   20.0,
 dz_top    =   50.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 0,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 0,
 output_srs       = 0,
 output_sgs       = 0,
 output_sus       = 0,
 output_shs       = 0,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 0,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 1,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 0,
 output_kh        = 0,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 0,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   400000.0,
 les_subdomain_ylen     =   400000.0,
 les_subdomain_dlen     =   400000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .true.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =   43200.0,
 lsnudge_start      =       0.0,
 lsnudge_end        =    9.0e30,
 lsnudge_ramp_time  =     900.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.8,
 side_cd      =      0.8,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =     -90.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_ib_windtunnel/README
================================================

 Test case using immersed boundary method.  (testcase=12)

 Based on wind tunnel data published by Martinuzzi and Tropea (1993,
 Journal of Fluids Engineering).

 Note: default resolution is rather coarse (50 grid points across channel).
 This default setup is designed to be inexpensive, for users to get started
 quickly.  Journal-quality simulations should use higher resolution.



================================================
FILE: run/config_files/les_ib_windtunnel/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_ib_windtunnel/namelist.input
================================================

 &param0
 nx           =     500,
 ny           =     200,
 nz           =      50,
 ppnode       =     128,
 timeformat   =       1,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 outunits     =       2,
 /

 &param1
 dx     =     0.001,
 dy     =     0.001,
 dz     =     0.001,
 dtl    =   0.00002,
 timax  =     0.5,
 run_time =  -999.9,
 tapfrq =     0.01,
 rstfrq =     0.5,
 statfrq =    0.0025,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  = 12,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  0,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  0,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  0,
 irdamp    =  0,
 hrdamp    =  0,
 psolver   =  6,
 ptype     =  5,
 ihail     =  1,
 iautoc    =  1,
 icor      =  0,
 betaplane =  0,
 lspgrad   =  4,
 eqtset    =  1,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  2,
 ebc       =  2,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  3,
 irbc      =  2,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  1,
 iwnd      =  6,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 15000.0,
 xhd     = 100000.0,
 alphobc =  0.0001,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    250.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =    100.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      0,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.00,
 cnst_lhflx = 0.0e-5,
 set_znt    =      1,
 cnst_znt   = 2.5e-6,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  =    0.1,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = 18000.0,
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 2,
 ptc_top   = 0.0,
 ptc_bot   = 0.0,
 viscosity = 1.5e-5,
 pr_num    = 1.00,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 0,
 output_sws       = 0,
 output_svs       = 0,
 output_sps       = 0,
 output_srs       = 0,
 output_sgs       = 0,
 output_sus       = 0,
 output_shs       = 0,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 0,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 0,
 output_thpert    = 0,
 output_prs       = 0,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 0,
 output_qvpert    = 0,
 output_q         = 0,
 output_dbz       = 0,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 restart_reset_frqtim  =  .true.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq      =       0.01,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   400000.0,
 les_subdomain_ylen     =   400000.0,
 les_subdomain_dlen     =   400000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .true.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =    0.05,
 recycle_cap_loc_m   =   0.125,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .true.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_ShallowCu/README
================================================

  Shallow cumulus convection using Large Eddy Simulation (LES)
  following Siebesma et al (2003, JAS, pg 1201).  Based on observations
  from the Barbados Oceanographic and Meteorological Experiment (BOMEX).



================================================
FILE: run/config_files/les_ShallowCu/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_ShallowCu/namelist.input
================================================

 &param0
 nx           =      64,
 ny           =      64,
 nz           =      75,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =   100.0,
 dy     =   100.0,
 dz     =    40.0,
 dtl    =   3.000,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq = 10800.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  3,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  2,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  2,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 19,
 iwnd      =  9,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.376e-4,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  2500.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      7.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx = 8.0e-3,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      1,
 cnst_ust   =   0.28,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = 18000.0,
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_ShallowCuLand/README
================================================

  Shallow cumulus convection over land using Large Eddy Simulation (LES)
  following Brown et al. (2002, QJRMS, 128, p 1075).  Based on observations
  from ARM-SGP.



================================================
FILE: run/config_files/les_ShallowCuLand/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_ShallowCuLand/namelist.input
================================================

 &param0
 nx           =      96,
 ny           =      96,
 nz           =     110,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    66.6667,
 dy     =    66.6667,
 dz     =    40.0,
 dtl    =  20.000,
 timax  = 54000.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq = 21600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  = 14,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  2,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  6,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  1,
 eqtset    =  1,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 23,
 iwnd      =  6,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 8.5e-5,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  3500.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      5,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx = 1.2113381E-02,
 cnst_lhflx = 3.8162874E-05,
 set_znt    =      1,
 cnst_znt   =   0.035,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      =  1500.0,
 str_bot   =  1000.0,
 str_top   =  1500.0,
 dz_bot    =     5.0,
 dz_top    =    35.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 1,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_ShallowCuPrecip/README
================================================

  Precipitating shallow cumulus convection using Large Eddy Simulation (LES)
  following vanZanten et al (2011, JAMES, doi:10.1029/2011MS000056).  Based on
  observations from the Rain in Cumulus over the Ocean (RICO) field campaign.



================================================
FILE: run/config_files/les_ShallowCuPrecip/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_ShallowCuPrecip/namelist.input
================================================

 &param0
 nx           =     128,
 ny           =     128,
 nz           =     100,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =   100.0,
 dy     =   100.0,
 dz     =    40.0,
 dtl    =   5.000,
 timax  = 86400.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq = 21600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  7,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  2,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  2,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 20,
 iwnd      = 11,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.451e-4,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  3000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =     70.0,
 nt_c    =     70.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.80,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      1,
 pertflx    =      0,
 cnstce     =  0.001133,
 cnstcd     =  0.001229,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =    0.0,
 cnst_lhflx =    0.0,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      =  1500.0,
 str_bot   =  1000.0,
 str_top   =  1500.0,
 dz_bot    =     5.0,
 dz_top    =    35.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_ShearBoundLayer/README
================================================

  Neutral, sheared boundary layer (SBL) using Large Eddy Simulation (LES)
  following Moeng and Sullivan (1994, JAS, pg 999).



================================================
FILE: run/config_files/les_ShearBoundLayer/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_ShearBoundLayer/namelist.input
================================================

 &param0
 nx           =      96,
 ny           =      96,
 nz           =      96,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    32.0,
 dy     =    32.0,
 dz     =    10.0,
 dtl    =   1.000,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq = 10800.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  2,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  1,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 18,
 iwnd      =  6,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 1.000e-4,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =   800.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      5,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    1.0,
 lu0        =      3,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx =   0.05,
 cnst_lhflx =   0.00,
 set_znt    =      1,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      =  1500.0,
 str_bot   =   800.0,
 str_top   =  1500.0,
 dz_bot    =   10.0,
 dz_top    =   77.5,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_StableBoundLayer/README
================================================

  Stable boundary layer using Large Eddy Simulation (LES)
  following Beare et al. (2006, BLM), doi:10.1007/s10546-004-2820-6



================================================
FILE: run/config_files/les_StableBoundLayer/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_StableBoundLayer/namelist.input
================================================

 &param0
 nx           =     128,
 ny           =     128,
 nz           =     128,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =   3.125,
 dy     =   3.125,
 dz     =   3.125,
 dtl    =   1.000,
 timax  = 32400.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq = 10800.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  9,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  0,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  2,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  1,
 eqtset    =  1,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 22,
 iwnd      =  6,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 1.390e-4,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =   300.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  4.0,
 vmove   =  0.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      5,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 265.00,
 tmn0       = 265.00,
 xland0     =    1.0,
 lu0        =      3,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.05,
 cnst_lhflx =   0.00,
 set_znt    =      1,
 cnst_znt   =   0.10,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 3600.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      =  1500.0,
 str_bot   =   800.0,
 str_top   =  1500.0,
 dz_bot    =   10.0,
 dz_top    =   77.5,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_StratoCuDrizzle/README
================================================

  Drizzling stratocumulus using Large Eddy Simulation (LES)
  following Ackerman et al (2009, MWR, pg 1083).  Based on observations
  from the second research flight (RF02) of the second Dynamics and Chemistry
  of Marine Stratocumulus (DYCOMS-II) field study.



================================================
FILE: run/config_files/les_StratoCuDrizzle/input_grid_z
================================================
    2.5
    7.6
   12.9
   18.6
   24.7
   31.4
   38.9
   47.2
   56.4
   66.7
   78.0
   90.4
  104.0
  118.8
  134.8
  152.0
  170.3
  189.7
  210.2
  231.6
  253.9
  277.0
  300.8
  325.1
  349.8
  374.9
  400.0
  425.1
  450.2
  474.9
  499.2
  523.0
  546.1
  568.4
  589.8
  610.3
  629.7
  648.0
  665.2
  681.2
  696.0
  709.6
  722.0
  733.3
  743.6
  752.8
  761.1
  768.6
  775.3
  781.4
  787.1
  792.4
  797.5
  802.5
  807.5
  812.5
  817.5
  822.5
  827.5
  832.5
  837.5
  842.5
  847.5
  852.5
  857.5
  862.5
  867.5
  872.5
  877.5
  882.5
  887.5
  892.5
  897.5
  902.5
  907.5
  912.5
  917.5
  922.5
  927.5
  932.9
  939.0
  946.3
  955.4
  966.7
  980.7
  998.1
 1019.1
 1044.4
 1074.4
 1109.7
 1150.7
 1198.0
 1251.9
 1313.2
 1382.1
 1459.3



================================================
FILE: run/config_files/les_StratoCuDrizzle/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_StratoCuDrizzle/namelist.input
================================================

 &param0
 nx           =     128,
 ny           =     128,
 nz           =      96,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    50.0,
 dy     =    50.0,
 dz     =     5.0,
 dtl    =   5.000,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq =  7200.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  5,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  2,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  1,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 15,
 iwnd      = 10,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 7.599433576e-5,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  1250.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =     55.0,
 nt_c    =     55.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx = 1.3170457E-02,
 cnst_lhflx = 3.0743802E-05,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      1,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  3,
 ztop      =  1500.0,
 str_bot   =  1000.0,
 str_top   =  1500.0,
 dz_bot    =     5.0,
 dz_top    =    35.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/les_StratoCuNoPrecip/README
================================================

  Nocturnal marine nonprecipitating stratocumulus using Large Eddy Simulation
  (LES) following Stevens et al (2005, MWR, pg 1443).  Based on observations
  from the first research flight (RF01) of the second Dynamics and Chemistry
  of Marine Stratocumulus (DYCOMS-II) field study.



================================================
FILE: run/config_files/les_StratoCuNoPrecip/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/les_StratoCuNoPrecip/namelist.input
================================================

 &param0
 nx           =      96,
 ny           =      96,
 nz           =     225,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    35.0,
 dy     =    35.0,
 dz     =     5.0,
 dtl    =   5.000,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =  3600.0,
 rstfrq =  7200.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  4,
 adapt_dt  =  1,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  2,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  6,
 ihail     =  0,
 iautoc    =  0,
 icor      =  1,
 lspgrad   =  1,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      = 15,
 iwnd      =  6,
 itern     =  0,
 iinit     =  0,
 irandp    =  1,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.376e-4,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  1000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx = 1.2113381E-02,
 cnst_lhflx = 3.8162874E-05,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      1,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      =  1500.0,
 str_bot   =  1000.0,
 str_top   =  1500.0,
 dz_bot    =     5.0,
 dz_top    =    35.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 1,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/nh_mountain_waves/README
================================================

  Nonhydrostatic mountain waves, 2D simulation.

  Based on Dudhia (1993, MWR, pg 1499).



================================================
FILE: run/config_files/nh_mountain_waves/namelist.input
================================================

 &param0
 nx           =     100,
 ny           =       1,
 nz           =     100,
 ppnode       =     128,
 timeformat   =       1,
 timestats    =       1,
 terrain_flag = .true.,
 procfiles    = .false.,
 /

 &param1
 dx     =   200.0,
 dy     =   200.0,
 dz     =   200.0,
 dtl    =   2.000,
 timax  =  2160.0,
 run_time =  -999.9,
 tapfrq =   216.0,
 rstfrq = -3600.0,
 statfrq =  -60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  0,
 testcase  =  0,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  1,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  1,
 lspgrad   =  1,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  2,
 ebc       =  2,
 sbc       =  1,
 nbc       =  1,
 bbc       =  1,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  9,
 iwnd      =  6,
 itern     =  1,
 iinit     =  0,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00010,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  14000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    250.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      0,
 sfcmodel   =      0,
 oceanmodel =      0,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = 18000.0,
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 1,
 output_interp    = 1,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 0,
 output_sfcparams = 0,
 output_sfcdiags  = 0,
 output_psfc      = 0,
 output_zs        = 1,
 output_zh        = 1,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/scm_HurrBoundLayer/README
================================================

  Simple hurricane boundary layer (HBL) using single column modeling (SCM)
  following Bryan et al (2017, BLM, pg 475).



================================================
FILE: run/config_files/scm_HurrBoundLayer/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/scm_HurrBoundLayer/namelist.input
================================================

 &param0
 nx           =       1,
 ny           =       1,
 nz           =     128,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    40.0,
 dy     =    40.0,
 dz     =    20.0,
 dtl    =   1.000,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =   300.0,
 rstfrq = 10800.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  2,
 testcase  =  6,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  0,
 ipbl      =  2,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  0,
 iautoc    =  0,
 cuparam   =  0,
 icor      =  1,
 lspgrad   =  3,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  8,
 iwnd      =  8,
 itern     =  0,
 iinit     =  0,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  2000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      0.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 301.15,
 tmn0       = 299.15,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      1,
 cnst_shflx =   0.10,
 cnst_lhflx =   0.00,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      =  2980.0,
 str_bot   =  2000.0,
 str_top   =  2980.0,
 dz_bot    =   20.0,
 dz_top    =   50.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/scm_HurrBoundLayer_tqnudge/README
================================================

  Simple hurricane boundary layer (HBL) using single column modeling (SCM)
  following Bryan et al (2017, BLM, pg 475) and Chen et al. (2021, JAS,
  pg 3559).

  cm1r19.10:  added a nudging term for theta and qv, and turned on moisture.
  Allows for stratification and surface heat fluxes.



================================================
FILE: run/config_files/scm_HurrBoundLayer_tqnudge/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/scm_HurrBoundLayer_tqnudge/namelist.input
================================================

 &param0
 nx           =       1,
 ny           =       1,
 nz           =     128,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =    40.0,
 dy     =    40.0,
 dz     =    20.0,
 dtl    =   1.000,
 timax  = 21600.0,
 run_time =  -999.9,
 tapfrq =   300.0,
 rstfrq = 10800.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  2,
 testcase  = 10,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  2,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  6,
 ihail     =  0,
 iautoc    =  0,
 cuparam   =  0,
 icor      =  1,
 lspgrad   =  3,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  8,
 iwnd      =  8,
 itern     =  0,
 iinit     =  0,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      =  2000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =     -1.0,
 l_h     =      0.0,
 lhref1  =      0.0,
 lhref2  =      0.0,
 l_inf   =     75.0,
 ndcnst  =    100.0,
 nt_c    =    100.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      1,
 oceanmodel =      1,
 initsfc    =      1,
 tsk0       = 301.15,
 tmn0       = 299.15,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.0011,
 cnstcd     =  0.0011,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.10,
 cnst_lhflx =   0.00,
 set_znt    =      0,
 cnst_znt   =   0.00,
 set_ust    =      0,
 cnst_ust   =   0.00,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      =  2980.0,
 str_bot   =  2000.0,
 str_top   =  2980.0,
 dz_bot    =   20.0,
 dz_top    =   50.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 2,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 1,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 1,
 output_def       = 1,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 1,
 output_lwp       = 1,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 1,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .true.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/sea_breeze/README
================================================

  Simple sea breeze test case, adapted from the WRF Model.



================================================
FILE: run/config_files/sea_breeze/input_sounding
================================================
   1000.0         300.5000        5.00000
   125.0000       300.5010        5.00000      0.0000000E+00  0.0000000E+00
   375.0000       300.5650        5.00000      0.0000000E+00  0.0000000E+00
   625.0000       301.0699        5.00000      0.0000000E+00  0.0000000E+00
   875.0000       301.6293        5.00000      0.0000000E+00  0.0000000E+00
   1125.000       302.2307        5.00000      0.0000000E+00  0.0000000E+00
   1375.000       302.8666        5.00000      0.0000000E+00  0.0000000E+00
   1625.000       303.5323        5.00000      0.0000000E+00  0.0000000E+00
   1875.000       304.2242        5.00000      0.0000000E+00  0.0000000E+00
   2125.000       304.9395        5.00000      0.0000000E+00  0.0000000E+00
   2375.000       305.6764        5.00000      0.0000000E+00  0.0000000E+00
   2625.000       306.4329        5.00000      0.0000000E+00  0.0000000E+00
   2875.000       307.2076        5.00000      0.0000000E+00  0.0000000E+00
   3125.000       307.9994        5.00000      0.0000000E+00  0.0000000E+00
   3375.000       308.8071        5.00000      0.0000000E+00  0.0000000E+00
   3625.000       309.6300        5.00000      0.0000000E+00  0.0000000E+00
   3875.000       310.4672       4.614990      0.0000000E+00  0.0000000E+00
   4125.000       311.3181       4.124146      0.0000000E+00  0.0000000E+00
   4375.000       312.1819       3.678759      0.0000000E+00  0.0000000E+00
   4625.000       313.0581       3.275154      0.0000000E+00  0.0000000E+00
   4875.000       313.9464       2.909960      0.0000000E+00  0.0000000E+00
   5125.000       314.8460       2.580028      0.0000000E+00  0.0000000E+00
   5375.000       315.7567       2.282451      0.0000000E+00  0.0000000E+00
   5625.000       316.6780       2.014546      0.0000000E+00  0.0000000E+00
   5875.000       317.6097       1.773806      0.0000000E+00  0.0000000E+00
   6125.000       318.5513       1.557917      0.0000000E+00  0.0000000E+00
   6375.000       319.5026       1.364712      0.0000000E+00  0.0000000E+00
   6625.000       320.4632       1.192196      0.0000000E+00  0.0000000E+00
   6875.000       321.4330       1.038515      0.0000000E+00  0.0000000E+00
   7125.000       322.4116      0.9019489      0.0000000E+00  0.0000000E+00
   7375.000       323.3988      0.7808990      0.0000000E+00  0.0000000E+00
   7625.000       324.3945      0.6738972      0.0000000E+00  0.0000000E+00
   7875.000       325.3983      0.5795774      0.0000000E+00  0.0000000E+00
   8125.000       326.4102      0.4966844      0.0000000E+00  0.0000000E+00
   8375.000       327.4298      0.4240607      0.0000000E+00  0.0000000E+00
   8625.000       328.4571      0.3606393      0.0000000E+00  0.0000000E+00
   8875.000       329.4919      0.3054438      0.0000000E+00  0.0000000E+00
   9125.000       330.5339      0.2575793      0.0000000E+00  0.0000000E+00
   9375.000       331.5832      0.2162281      0.0000000E+00  0.0000000E+00
   9625.000       332.6394      0.1806441      0.0000000E+00  0.0000000E+00
   9875.000       333.7025      0.1501510      0.0000000E+00  0.0000000E+00
   10125.00       334.7725      0.1241341      0.0000000E+00  0.0000000E+00
   10375.00       335.8490      0.1020380      0.0000000E+00  0.0000000E+00
   10625.00       336.9320      8.3363235E-02  0.0000000E+00  0.0000000E+00
   10875.00       338.0214      6.7661338E-02  0.0000000E+00  0.0000000E+00
   11125.00       339.1171      5.4530919E-02  0.0000000E+00  0.0000000E+00
   11375.00       340.2190      4.3614354E-02  0.0000000E+00  0.0000000E+00
   11625.00       341.3269      3.4594502E-02  0.0000000E+00  0.0000000E+00
   11875.00       342.4408      2.7190926E-02  0.0000000E+00  0.0000000E+00
   12125.00       344.9724      2.4574272E-02  0.0000000E+00  0.0000000E+00
   12375.00       348.9513      2.5715416E-02  0.0000000E+00  0.0000000E+00
   12625.00       352.9761      2.6911106E-02  0.0000000E+00  0.0000000E+00
   12875.00       357.0473      2.8164061E-02  0.0000000E+00  0.0000000E+00
   13125.00       361.1655      2.9477064E-02  0.0000000E+00  0.0000000E+00
   13375.00       365.3311      3.0853137E-02  0.0000000E+00  0.0000000E+00
   13625.00       369.5448      3.2295462E-02  0.0000000E+00  0.0000000E+00
   13875.00       373.8072      3.3807345E-02  0.0000000E+00  0.0000000E+00
   14125.00       378.1187      3.5392068E-02  0.0000000E+00  0.0000000E+00
   14375.00       382.4798      3.7053265E-02  0.0000000E+00  0.0000000E+00
   14625.00       386.8913      3.8795106E-02  0.0000000E+00  0.0000000E+00
   14875.00       391.3537      4.0621303E-02  0.0000000E+00  0.0000000E+00
   15125.00       395.8676      4.2536203E-02  0.0000000E+00  0.0000000E+00
   15375.00       400.4335      4.4544484E-02  0.0000000E+00  0.0000000E+00
   15625.00       405.0521      4.6650380E-02  0.0000000E+00  0.0000000E+00
   15875.00       409.7239      4.8859127E-02  0.0000000E+00  0.0000000E+00
   16125.00       414.4497      5.1176008E-02  0.0000000E+00  0.0000000E+00
   16375.00       419.2299      5.3606406E-02  0.0000000E+00  0.0000000E+00
   16625.00       424.0653      5.6155890E-02  0.0000000E+00  0.0000000E+00
   16875.00       428.9565      5.8831204E-02  0.0000000E+00  0.0000000E+00
   17125.00       433.9040      6.1637800E-02  0.0000000E+00  0.0000000E+00
   17375.00       438.9086      6.4582929E-02  0.0000000E+00  0.0000000E+00
   17625.00       443.9710      6.7673884E-02  0.0000000E+00  0.0000000E+00
   17875.00       449.0917      7.0917897E-02  0.0000000E+00  0.0000000E+00
   18125.00       454.2715      7.4322589E-02  0.0000000E+00  0.0000000E+00
   18375.00       459.5110      7.7896632E-02  0.0000000E+00  0.0000000E+00
   18625.00       464.8110      8.1648715E-02  0.0000000E+00  0.0000000E+00
   18875.00       470.1721      8.5588045E-02  0.0000000E+00  0.0000000E+00
   19125.00       475.5951      8.9724302E-02  0.0000000E+00  0.0000000E+00
   19375.00       481.0806      9.4000000E-02  0.0000000E+00  0.0000000E+00
   19625.00       486.6293      9.4000000E-02  0.0000000E+00  0.0000000E+00
   19875.00       492.2421      9.4000000E-02  0.0000000E+00  0.0000000E+00



================================================
FILE: run/config_files/sea_breeze/LANDUSE.TBL
================================================
USGS
33,2, 'ALBD   SLMO   SFEM   SFZ0 THERIN   SCFX   SFHC   '
SUMMER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      17.,   .30,  .985,   15.,    4.,  2.71, 25.0e5,'Dryland Cropland and Pasture'
3,      18.,   .50,  .985,   10.,    4.,  2.20, 25.0e5,'Irrigated Cropland and Pasture'
4,      18.,   .25,  .985,   15.,    4.,  2.56, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      18.,   .25,   .98,   14.,    4.,  2.56, 25.0e5,'Cropland/Grassland Mosaic'
6,      16.,   .35,  .985,   20.,    4.,  3.19, 25.0e5,'Cropland/Woodland Mosaic'
7,      19.,   .15,   .96,   12.,    3.,  2.37, 20.8e5,'Grassland'
8,      22.,   .10,   .93,    5.,    3.,  1.56, 20.8e5,'Shrubland'
9,      20.,   .15,   .95,    6.,    3.,  2.14, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     16.,   .30,   .93,   50.,    4.,  2.63, 25.0e5,'Deciduous Broadleaf Forest'
12,     14.,   .30,   .94,   50.,    4.,  2.86, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .30,   .95,   50.,    4.,  3.33, 29.2e5,'Evergreen Needleleaf Forest'
15,     13.,   .30,   .97,   50.,    4.,  2.11, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .60,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .35,   .95,   40.,    5.,  1.14, 41.8e5,'Wooded Wetland'
19,     25.,   .02,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .50,   .92,   10.,    5.,  2.87, 9.0e25,'Herbaceous Tundra'
21,     15.,   .50,   .93,   30.,    5.,  2.67, 9.0e25,'Wooded Tundra'
22,     15.,   .50,   .92,   15.,    5.,  2.67, 9.0e25,'Mixed Tundra'
23,     25.,   .02,   .90,   10.,    2.,  1.60, 12.0e5,'Bare Ground Tundra'
24,     55.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     30.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .50,   .95,   15.,    6.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'
WINTER
1,      15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Urban and Built-Up Land'
2,      20.,   .60,   .92,    5.,    4.,  2.00, 25.0e5,'Dryland Cropland and Pasture'
3,      20.,   .50,   .93,    2.,    4.,  1.76, 25.0e5,'Irrigated Cropland and Pasture'
4,      20.,   .50,   .92,    5.,    4.,  2.00, 25.0e5,'Mixed Dryland/Irrigated Cropland and Pasture'
5,      20.,   .40,   .92,    5.,    4.,  2.00, 25.0e5,'Cropland/Grassland Mosaic'
6,      20.,   .60,   .93,   20.,    4.,  2.00, 25.0e5,'Cropland/Woodland Mosaic'
7,      23.,   .30,   .92,   10.,    4.,  2.00, 20.8e5,'Grassland'
8,      22.,   .20,   .93,    1.,    4.,  1.30, 20.8e5,'Shrubland'
9,      22.,   .25,   .93,    1.,    4.,  1.24, 20.8e5,'Mixed Shrubland/Grassland'
10,     20.,   .15,   .92,   15.,    3.,  2.00, 25.0e5,'Savanna'
11,     17.,   .60,   .93,   50.,    5.,  2.40, 25.0e5,'Deciduous Broadleaf Forest'
12,     15.,   .60,   .93,   50.,    5.,  2.60, 25.0e5,'Deciduous Needleleaf Forest'
13,     12.,   .50,   .95,   50.,    5.,  1.67, 29.2e5,'Evergreen Broadleaf Forest'
14,     12.,   .60,   .95,   50.,    5.,  3.00, 29.2e5,'Evergreen Needleleaf Forest'
15,     14.,   .60,   .93,   20.,    6.,  1.12, 41.8e5,'Mixed Forest'
16,      8.,   1.0,   .98,  0.01,    6.,    0., 9.0e25,'Water Bodies'
17,     14.,   .75,   .95,   20.,    6.,  1.50, 29.2e5,'Herbaceous Wetland'
18,     14.,   .70,   .95,   40.,    6.,  1.14, 41.8e5,'Wooded Wetland'
19,     23.,   .05,   .90,    1.,    2.,  0.81, 12.0e5,'Barren or Sparsely Vegetated'
20,     15.,   .60,   .92,   10.,    5.,  2.00, 9.0e25,'Herbaceous Tundra'
21,     15.,   .60,   .93,   30.,    5.,  1.75, 9.0e25,'Wooded Tundra'
22,     15.,   .60,   .92,   15.,    5.,  1.75, 9.0e25,'Mixed Tundra'
23,     25.,   .05,   .90,    5.,    5.,  1.80, 12.0e5,'Bare Ground Tundra'
24,     70.,   .95,   .95,   0.1,    5.,    0., 9.0e25,'Snow or Ice'
25,     40.,   .40,   .90,    1.,    5.,   .62, 12.0E5,'Playa'
26,     18.,   .40,   .95,   15.,    5.,   .62, 12.0E5,'Lava'
27,     70.,   .40,   .90,    1.,    5.,    0., 12.0E5,'White Sand'
28,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
29,     15.,   .02,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
30,     15.,   .10,   .88,   80.,    3.,  1.67, 18.9e5,'Unassigned'
31,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Low Intensity Residential '
32,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'High Intensity Residential'
33,     10.,   .10,   .97,   80.,    3.,  1.67, 18.9e5,'Industrial or Commercial'



================================================
FILE: run/config_files/sea_breeze/namelist.input
================================================

 &param0
 nx           =     201,
 ny           =       1,
 nz           =      34,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =  1000.0,
 dy     =  1000.0,
 dz     =   588.235,
 dtl    =  15.000,
 timax  = 43200.0,
 run_time =  -999.9,
 tapfrq =  1800.0,
 rstfrq = -3600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  2,
 testcase  =  0,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  1,
 sgsmodel  =  1,
 tconfig   =  2,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  1,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  0,
 lspgrad   =  0,
 eqtset    =  2,
 idiss     =  0,
 efall     =  0,
 rterm     =  0,
 wbc       =  1,
 ebc       =  1,
 sbc       =  1,
 nbc       =  1,
 bbc       =  3,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  7,
 iwnd      =  0,
 itern     =  0,
 iinit     =  0,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  0,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 15000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   =  0.0,
 vmove   =  0.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 v_t     =      7.0,
 l_inf   =     75.0,
 ndcnst  =    250.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        2,
 dtrad   =    300.0,
 ctrlat  =    30.00,
 ctrlon  =     0.00,
 year    =     2007,
 month   =        6,
 day     =        1,
 hour    =        5,
 minute  =       00,
 second  =       00,
 /

 &param12
 isfcflx    =      1,
 sfcmodel   =      3,
 oceanmodel =      1,
 initsfc    =      2,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  1,
 ztop      = 20000.16,
 str_bot   =     0.0,
 str_top   = 20000.16,
 dz_bot    =    62.0,
 dz_top    =  1114.48,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 1,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 1,
 output_sfcparams = 1,
 output_sfcdiags  = 1,
 output_psfc      = 0,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 1,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 1,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 0,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 0,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/squall_line/README
================================================

  Idealized squall line simulation, mostly following Bryan et al (2003,
  MWR, pg 2394).

  Default configuration is the 1-km weak-shear case.



================================================
FILE: run/config_files/squall_line/namelist.input
================================================

 &param0
 nx           =     300,
 ny           =      60,
 nz           =      40,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =  1000.0,
 dy     =  1000.0,
 dz     =   500.0,
 dtl    =   6.000,
 timax  = 10800.0,
 run_time =  -999.9,
 tapfrq =   900.0,
 rstfrq = -3600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  0,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  1,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  0,
 lspgrad   =  0,
 eqtset    =  2,
 idiss     =  1,
 efall     =  0,
 rterm     =  0,
 wbc       =  2,
 ebc       =  2,
 sbc       =  1,
 nbc       =  1,
 bbc       =  1,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  5,
 iwnd      =  1,
 itern     =  0,
 iinit     =  8,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  1,
 axisymm   =  0,
 imove     =  1,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 15000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  0.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    250.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      0,
 sfcmodel   =      0,
 oceanmodel =      0,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = 18000.0,
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 1,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 1,
 output_sfcflx    = 0,
 output_sfcparams = 0,
 output_sfcdiags  = 0,
 output_psfc      = 0,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 0,
 output_pv        = 0,
 output_uh        = 0,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 1,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 0,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /



================================================
FILE: run/config_files/supercell/README
================================================

  Idealized supercell thunderstorm simulation, following
  Weisman and Rotunno (2000, JAS, pg 1452).

  Configuration is the 1/4-Circle hodograph case.



================================================
FILE: run/config_files/supercell/namelist.input
================================================

 &param0
 nx           =     120,
 ny           =     120,
 nz           =      40,
 ppnode       =     128,
 timeformat   =       2,
 timestats    =       1,
 terrain_flag = .false.,
 procfiles    = .false.,
 /

 &param1
 dx     =  1000.0,
 dy     =  1000.0,
 dz     =   500.0,
 dtl    =   6.000,
 timax  =  7200.0,
 run_time =  -999.9,
 tapfrq =   900.0,
 rstfrq = -3600.0,
 statfrq =   60.0,
 prclfrq =   60.0,
 /

 &param2
 cm1setup  =  1,
 testcase  =  0,
 adapt_dt  =  0,
 irst      =  0,
 rstnum    =  1,
 iconly    =  0,
 hadvordrs =  5,
 vadvordrs =  5,
 hadvordrv =  5,
 vadvordrv =  5,
 advwenos  =  2,
 advwenov  =  0,
 weno_order = 5,
 apmasscon =  1,
 idiff     =  0,
 mdiff     =  0,
 difforder =  6,
 imoist    =  1,
 ipbl      =  0,
 sgsmodel  =  1,
 tconfig   =  1,
 bcturbs   =  1,
 horizturb =  0,
 doimpl    =  1,
 irdamp    =  1,
 hrdamp    =  0,
 psolver   =  3,
 ptype     =  5,
 ihail     =  1,
 iautoc    =  1,
 cuparam   =  0,
 icor      =  0,
 lspgrad   =  0,
 eqtset    =  2,
 idiss     =  1,
 efall     =  0,
 rterm     =  0,
 wbc       =  2,
 ebc       =  2,
 sbc       =  2,
 nbc       =  2,
 bbc       =  1,
 tbc       =  1,
 irbc      =  4,
 roflux    =  0,
 nudgeobc  =  0,
 isnd      =  5,
 iwnd      =  2,
 itern     =  0,
 iinit     =  1,
 irandp    =  0,
 ibalance  =  0,
 iorigin   =  2,
 axisymm   =  0,
 imove     =  1,
 iptra     =  0,
 npt       =  1,
 pdtra     =  1,
 iprcl     =  0,
 nparcels  =  1,
 /

 &param3
 kdiff2  =   75.0,
 kdiff6  =   0.040,
 fcor    = 0.00005,
 kdiv    = 0.10,
 alph    = 0.60,
 rdalpha = 3.3333333333e-3,
 zd      = 15000.0,
 xhd     = 100000.0,
 alphobc = 60.0,
 umove   = 12.5,
 vmove   =  3.0,
 v_t     =      7.0,
 l_h     =    100.0,
 lhref1  =    100.0,
 lhref2  =   1000.0,
 l_inf   =     75.0,
 ndcnst  =    250.0,
 nt_c    =    250.0,
 csound  =    300.0,
 cstar   =     30.0,
 /

 &param11
 radopt  =        0,
 dtrad   =    300.0,
 ctrlat  =    36.68,
 ctrlon  =   -98.35,
 year    =     2009,
 month   =        5,
 day     =       15,
 hour    =       21,
 minute  =       38,
 second  =       00,
 /

 &param12
 isfcflx    =      0,
 sfcmodel   =      0,
 oceanmodel =      0,
 initsfc    =      1,
 tsk0       = 299.28,
 tmn0       = 297.28,
 xland0     =    2.0,
 lu0        =     16,
 season     =      1,
 cecd       =      3,
 pertflx    =      0,
 cnstce     =  0.001,
 cnstcd     =  0.001,
 isftcflx   =      0,
 iz0tlnd    =      0,
 oml_hml0   =   50.0,
 oml_gamma  =   0.14,
 set_flx    =      0,
 cnst_shflx =   0.24,
 cnst_lhflx = 5.2e-5,
 set_znt    =      0,
 cnst_znt   =   0.16,
 set_ust    =      0,
 cnst_ust   =   0.25,
 ramp_sgs   =      1,
 ramp_time  = 1800.0,
 t2p_avg   =       1,
 /

 &param4
 stretch_x =      0,
 dx_inner  =    1000.0,
 dx_outer  =    7000.0,
 nos_x_len =   40000.0,
 tot_x_len =  120000.0,
 /

 &param5
 stretch_y =      0,
 dy_inner  =    1000.0,
 dy_outer  =    7000.0,
 nos_y_len =   40000.0,
 tot_y_len =  120000.0,
 /

 &param6
 stretch_z =  0,
 ztop      = 18000.0,
 str_bot   =     0.0,
 str_top   =  2000.0,
 dz_bot    =   125.0,
 dz_top    =   500.0,
 /

 &param7
 bc_temp   = 1,
 ptc_top   = 250.0,
 ptc_bot   = 300.0,
 viscosity = 25.0,
 pr_num    = 0.72,
 /

 &param8
 var1      =   0.0,
 var2      =   0.0,
 var3      =   0.0,
 var4      =   0.0,
 var5      =   0.0,
 var6      =   0.0,
 var7      =   0.0,
 var8      =   0.0,
 var9      =   0.0,
 var10     =   0.0,
 var11     =   0.0,
 var12     =   0.0,
 var13     =   0.0,
 var14     =   0.0,
 var15     =   0.0,
 var16     =   0.0,
 var17     =   0.0,
 var18     =   0.0,
 var19     =   0.0,
 var20     =   0.0,
 /

 &param9
 output_format    = 1,
 output_filetype  = 1,
 output_interp    = 0,
 output_rain      = 1,
 output_sws       = 1,
 output_svs       = 1,
 output_sps       = 1,
 output_srs       = 1,
 output_sgs       = 1,
 output_sus       = 1,
 output_shs       = 1,
 output_coldpool  = 0,
 output_sfcflx    = 0,
 output_sfcparams = 0,
 output_sfcdiags  = 0,
 output_psfc      = 0,
 output_zs        = 0,
 output_zh        = 0,
 output_basestate = 0,
 output_th        = 1,
 output_thpert    = 0,
 output_prs       = 1,
 output_prspert   = 0,
 output_pi        = 0,
 output_pipert    = 0,
 output_rho       = 0,
 output_rhopert   = 0,
 output_tke       = 1,
 output_km        = 1,
 output_kh        = 1,
 output_qv        = 1,
 output_qvpert    = 0,
 output_q         = 1,
 output_dbz       = 1,
 output_buoyancy  = 0,
 output_u         = 1,
 output_upert     = 0,
 output_uinterp   = 1,
 output_v         = 1,
 output_vpert     = 0,
 output_vinterp   = 1,
 output_w         = 1,
 output_winterp   = 1,
 output_vort      = 1,
 output_pv        = 0,
 output_uh        = 1,
 output_pblten    = 0,
 output_dissten   = 0,
 output_fallvel   = 0,
 output_nm        = 0,
 output_def       = 0,
 output_radten    = 0,
 output_cape      = 0,
 output_cin       = 0,
 output_lcl       = 0,
 output_lfc       = 0,
 output_pwat      = 0,
 output_lwp       = 0,
 output_thbudget  = 0,
 output_qvbudget  = 0,
 output_ubudget   = 0,
 output_vbudget   = 0,
 output_wbudget   = 0,
 output_pdcomp    = 0,
 /

 &param16
 restart_format   = 1,
 restart_filetype = 2,
 restart_reset_frqtim  =  .true.,
 restart_file_theta    =  .false.,
 restart_file_dbz      =  .false.,
 restart_file_th0      =  .false.,
 restart_file_prs0     =  .false.,
 restart_file_pi0      =  .false.,
 restart_file_rho0     =  .false.,
 restart_file_qv0      =  .false.,
 restart_file_u0       =  .false.,
 restart_file_v0       =  .false.,
 restart_file_zs       =  .false.,
 restart_file_zh       =  .false.,
 restart_file_zf       =  .false.,
 restart_file_diags    =  .false.,
 restart_use_theta     =  .false.,
 /

 &param10
 stat_w        = 1,
 stat_wlevs    = 1,
 stat_u        = 1,
 stat_v        = 1,
 stat_rmw      = 0,
 stat_pipert   = 1,
 stat_prspert  = 1,
 stat_thpert   = 1,
 stat_q        = 1,
 stat_tke      = 1,
 stat_km       = 1,
 stat_kh       = 1,
 stat_div      = 1,
 stat_rh       = 1,
 stat_rhi      = 1,
 stat_the      = 1,
 stat_cloud    = 1,
 stat_sfcprs   = 1,
 stat_wsp      = 1,
 stat_cfl      = 1,
 stat_vort     = 1,
 stat_tmass    = 1,
 stat_tmois    = 1,
 stat_qmass    = 1,
 stat_tenerg   = 1,
 stat_mo       = 1,
 stat_tmf      = 1,
 stat_pcn      = 1,
 stat_qsrc     = 1,
 /

 &param13
 prcl_th       = 1,
 prcl_t        = 1,
 prcl_prs      = 1,
 prcl_ptra     = 1,
 prcl_q        = 1,
 prcl_nc       = 1,
 prcl_km       = 1,
 prcl_kh       = 1,
 prcl_tke      = 1,
 prcl_dbz      = 1,
 prcl_b        = 1,
 prcl_vpg      = 1,
 prcl_vort     = 1,
 prcl_rho      = 1,
 prcl_qsat     = 1,
 prcl_sfc      = 1,
 /

 &param14
 dodomaindiag   =    .false.,
 diagfrq        =       60.0,
 /

 &param15
 doazimavg        =    .false.,
 azimavgfrq       =     3600.0,
 rlen             =   300000.0,
 do_adapt_move    =    .false.,
 adapt_move_frq   =     3600.0,
 /

 &param17
 les_subdomain_shape    =      1 ,
 les_subdomain_xlen     =   200000.0,
 les_subdomain_ylen     =   200000.0,
 les_subdomain_dlen     =   200000.0,
 les_subdomain_trnslen  =     5000.0,
 /

 &param18
 do_recycle_w        =  .false.,
 do_recycle_s        =  .false.,
 do_recycle_e        =  .false.,
 do_recycle_n        =  .false.,
 recycle_width_dx    =     6.0,
 recycle_depth_m     =  1500.0,
 recycle_cap_loc_m   =  4000.0,
 recycle_inj_loc_m   =     0.0,
 /

 &param19
 do_lsnudge         =    .false.,
 do_lsnudge_u       =    .false.,
 do_lsnudge_v       =    .false.,
 do_lsnudge_th      =    .false.,
 do_lsnudge_qv      =    .false.,
 lsnudge_tau        =    1800.0,
 lsnudge_start      =    3600.0,
 lsnudge_end        =    7200.0,
 lsnudge_ramp_time  =     600.0,
 /

 &param20
 do_ib        =    .false.,
 ib_init      =       4,
 top_cd       =      0.4,
 side_cd      =      0.4,
 /

 &param21
 hurr_vg       =      40.0,
 hurr_rad      =   40000.0,
 hurr_vgpl     =     -0.70,
 hurr_rotate   =       0.0,
 /

 &nssl2mom_params
   alphah  = 0,     ! shape parameter of graupel
   alphahl = 0.5,   ! shape parameter of hail
   ccn     = 0.6e9  ! base ccn concentration; see README.namelist
   cnor    = 8.e6,  ! for single moment only
   cnoh    = 4.e4,  ! for single moment only
 /
