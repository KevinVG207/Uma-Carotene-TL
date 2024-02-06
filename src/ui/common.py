from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import math
import util
import os
import json

MDB_CAT_NAMES = {
    "text_data": {
        "1": "Error Descriptions",
        "2": "Errors",
        "3": "Tutorial",
        "4": "(Auto) Outfit+Chara Combo",
        "5": "Outfit Titles",
        "6": "Character Names",
        "7": "Voice Actors",
        "8": "Profile Residence",
        "9": "Profile Weight",
        "10": "Item Descr (Long Tap)",
        "13": "Gacha Descr",
        "14": "Clothes",
        "15": "Clothes Caption(?)",
        "16": "Song Names",
        "17": "Song Credits",
        "23": "Item Names",
        "24": "Item Descriptions",
        "25": "How to obtain items",
        "26": "Gacha Banners",
        "27": "?",
        "28": "Race Names (Long)",
        "29": "Race Names (Short)",
        "31": "Race Course Names",
        "32": "Race Names",
        "33": "Race Names",
        "34": "Race Course Names",
        "35": "Race City Names",
        "36": "Race Names",
        "38": "Race Names (Short)",
        "39": "Item Names 2",
        "40": "? Shop Descriptions",
        "41": "Item exchange conditions",
        "42": "Jewel Amounts",
        "47": "Skill Names",
        "48": "Skill Descriptions",
        "49": "Jewel Amounts",
        "55": "Training/Outing Types",
        "59": "Mob Uma Names",
        "63": "?",
        "64": "Reward Descriptions",
        "65": "Titles",
        "66": "Title Descriptions",
        "67": "Missions",
        "68": "Loading Screen Headers",
        "69": "Secrets/Tips/Comics",
        "70": "Login Bonus",
        "75": "(Auto) Support+Chara Combo",
        "76": "Support Card Titles",
        "77": "Character Names",
        "78": "Character Names (No Kanji)",
        "88": "Card Stories",
        "94": "Main Story Chapters",
        "113": "Chara Pieces",
        "119": "Scenario Names",
        "120": "Scenario Descr",
        "144": "Profile Slogan",
        "147": "Factors(?)",
        "151": "Support Events",
        "162": "Profile Grade",
        "163": "Profile Descr",
        "164": "Profile Strengths",
        "165": "Profile Weaknesses",
        "166": "Profile Ears",
        "167": "Profile Tail",
        "168": "Profile Shoe Size",
        "169": "Profile Family",
        "170": "Character Names",
        "172": "Factor details",
        "182": "Chara Names (katakana)",
        "189": "Story Event Titles",
        "191": "Story Event Chapters",
        "214": "Story Event Titles (Short)",
        "222": "Anniv. Story Chapters",
    }
}

# ErrorMessage = 1
# ErrorHeader = 2
# Tutorial = 3
# MasterCardTitleName = 5
# MasterCharaName = 6
# MasterCharaCv = 7
# MasterItemCommentForLongTap = 10
# MasterGachaMainDescription = 13
# MasterDressName = 14
# MasterDressCaption = 15
# MasterLiveTitle = 16
# MasterLiveAuthor = 17
# MasterItemName = 23
# MasterItemComment = 24
# MasterItemComment2 = 25
# MasterGachaName = 26
# MasterSingleModeAnalyzeMessage = 27
# MasterRaceInstanceName = 28
# MasterRaceInstanceShortName = 29
# MasterRaceTrackJikkyoName = 31
# MasterRaceName = 32
# MasterRaceJikkyoRaceName = 33
# MasterRaceTrackName = 34
# MasterRaceTrackShortName = 35
# MasterTrophyDetailRaceName = 36
# MasterTrophyListRaceName = 38
# MasterItemExchangeTopName = 39
# MasterItemExchangeTopDescription = 40
# MasterItemExchangeCondition = 41
# MasterItemJewelBreakDownName = 42
# MasterSkillName = 47
# MasterSkillExplain = 48
# MasterShopName = 49
# MasterSingleModeTrainingName = 55
# MasterMobName = 59
# MasterTutorialGuideDescription = 63
# MasterGiftMessage = 64
# MasterHonorName = 65
# MasterHonorExplain = 66
# MasterMissionName = 67
# MasterTopicsTitle = 68
# MasterTopicsComment = 69
# MasterLoginBonusName = 70
# MasterSupportCardTitleName = 76
# MasterSupportCardGroupName = 77
# MasterSupportCardGroupNameFurigana = 78
# MasterSupportCardStory = 88
# CharaStoryEpisodeTitle = 92
# MainStoryPartName = 93
# MainStoryEpisodeTitle = 94
# MainStoryConditionRaceBonus = 95
# MainStoryStoryNumberTitle = 96
# SingleModeTazunaComment = 97
# MasterSkillCondition = 110
# SingleModeWinsSaddleName = 111
# MainStoryPartTitle = 112
# MasterPieceName = 113
# MasterPieceDescription = 114
# SingleModeRouteTitle = 119
# SingleModeRouteDesc = 120
# SingleModeCharaGradeName = 121
# LiveMusicCaption = 128
# RaceMainReward = 129
# NickName = 130
# NickNameCondition = 131
# MasterDailyRaceGroupName = 132
# ItemGroupName = 133
# ExtraCharacterName = 136
# SingleModeCommandName = 138
# SingleModeEvaluationComment = 139
# TeamStadiumRawScoreName = 140
# TeamStadiumRawScoreDescription = 141
# SingleModeCharaEffectName = 142
# SingleModeCharaEffectDescription = 143
# MasterCharaCatchphrase = 144
# SuccessionFactorName = 147
# TeamStadiumScoreBonusName = 148
# UniqueEffectName = 150
# SupportCardEffectName = 151
# SupportCardEffectDescription = 154
# UniqueEffectDesciption = 155
# MasterCharaFormalName = 170
# MasterVoiceLockText = 171
# SuccessionFactorDescription = 172
# MasterProfileTitle = 175
# ItemFlavorText = 176
# StoryEventItem = 180
# SingleModeStoryTitle = 181
# MasterCharaFurigana = 182
# MasterLegendRaceGroupName = 183
# MasterPushNotificatiopnTPRecover = 184
# MasterPushNotificatiopnRPRecover = 185
# TeamStadiumSupportBonusTazunaComment = 186
# CampaignTitle = 187
# CampaignExplain = 188
# StoryEventTitle = 189
# StoryEventMissionName = 190
# StoryEventEpisodeTitle = 191
# MiniBgName = 192
# SingleModeScenarioTeamRaceHonor = 193
# SingleModeScenarioTeamRaceNpcTeamName = 194
# SingleModeScenarioTeamRaceTeamName = 195
# HomePosterDetail = 196
# ItemFlavorText2 = 197
# ScenarioLinkEvent = 198
# ScenarioLinkCard = 199
# ScenarioLinkSupportCard = 200
# MasterChampionsNewsRaceText = 201
# MasterChampionsNewsTrainerDetailText = 202
# MasterChampionsNewsCharacterDetailText = 203
# MasterChampionsNewsCharacterInterviewText = 204
# MasterChampionsNewsCharacterSelifText = 205
# MasterChampionsNewsRaceTitle = 206
# ScenarioLiveMasterBonus = 207
# ScenarioLiveLiveBonus = 208
# ScenarioLiveTreeName = 209
# ScenarioLiveSongName = 210
# ScenarioLiveTitle = 250
# ScenarioLiveUIText = 270
# EventAnnounceTitle = 211
# EventAnnounceInfo = 212
# StoryEventShortTitle = 214
# TransferEventDetailTitle = 215
# TransferEventDetailComment = 216
# TransferEventDetailCondition = 217
# TransferEventResultComment = 220
# MasterSingleModeScenarioTeamRaceRaceName = 218
# StoryExtraTitle = 221
# StoryExtraEpisodeTitle = 222
# SingleModeScenarioFreeItemName = 225
# SingleModeScenarioFreeItemDetailText = 226
# BgName = 223
# JikkyoSingleModeScenarioTeamRaceHonor = 227
# Jukebox = 228
# MasterChampionsExtraNewsTitleText = 229
# MasterChampionsExtraNewsRaceExplainText = 230
# MasterChampionsExtraNewsInterviewText = 231
# MasterChampionsExtraNewsCharacterText = 232
# SingleModeDifficulty = 233
# SingleModeDifficultyBox = 234
# SingleModeDifficultyGauge = 235
# CampaignFormalTitle = 236
# SingleModeScenarioShortName = 237
# SingleModeScenarioFreeItemAboutText = 238
# SingleModeDifficultyExplain = 239
# TrainingChallengeScenarioGimmickName = 240
# ChallengeMatchRawPointName = 243
# ChallengeMatchRawPointDescription = 244
# SingleModeDifficultyNpcRate = 245
# SingleModeDifficultyBoxDescription = 246
# SingleModeAchievementName = 247
# SingleModeAchievementInfo = 249
# LiveTheaterMusicCondition = 252
# FanRaidTitle = 248
# FanRaidNewLineTitle = 251
# FanRaidCommonRewardDialogComment = 253
# SingleModeDifficultyDataDescriptionText = 254
# SingleModeDifficultyDataDescriptionCompleteText = 255
# SingleModeDifficultyExplainAlert = 256
# TeamBuildingCollectionSetDescription = 257
# HomeBannerUrlConfirm = 266
# SingleModeGainSelectChoiceLabel = 267
# CampaignWalkingLocationName = 268
# HomeBannerUrlConfirmAlert = 269
# CampaignValentinePresentMessageMale = 271
# CampaignValentinePresentMessageFemale = 272
# CampaignValentinePresentName = 273
# HeroesGetSkillCondition = 275
# JukeboxSetListTitle = 276
# GachaNameWithIndention = 277
# CollectEventMapLoginBonusButtonDescription = 279
# CollectEventMapLoginBonusButtonTitle = 280
# CollectEventMapEventButtonDescription = 281
# CollectEventMapEventButtonTitle = 282
# CollectRaidTitle = 283
# CollectRaidGeneralRewardDialogComment = 284
# CollectRaidEpisodeTitle = 285
# CollectRaidButtonRewardReceivingTermText = 286
# CollectEventMapTitle = 287
# CollectEventMapEventNoticeDialogTitle = 288
# CollectEventMapEventNoticeDialogBody = 289
# SkillUpgrade1 = 290
# SingleModeScenarioVenusSpiritName = 295
# SingleModeScenarioVenusSpiritEffectGroupDetailText = 296
# SingleModeScenarioVenusSpiritEffect = 298
# SingleModeScenarioVenusScenarioRaceTitle = 299
# SingleModeScenarioVenusScenarioRaceShortTitle = 300
# SupportCardEffectFilterGroupName = 293
# SupportCardEffectFilterName = 294
# HeroesLotteryMessage = 297
# FactorResearchEventTitle = 301
# MapEventTitle = 302
# MapEventGaugeName = 303
# MapEventMapPointName = 304
# MapEventMovieText1 = 305
# MapEventMovieText2 = 306
# MapEventMovieText3 = 307
# MapEventEpisodeTitle = 308
# MapEventAreaName = 309
# MapEventTopHeaderTitle = 312
# SingleModeScenarioArcPotentialName = 310
# SingleModeScenarioArcPotentialBonusName = 311
# SingleModeScenarioArcPotentialCondition = 313
# SingleModeScenarioArcPotentialBuffName = 314
# SingleModeScenarioArcPotentialDeBuffName = 315
# SingleModeScenarioArcPotentialDeBuffDescription = 316
# SingleModeScenarioArcPotentialBonusEffectName = 317
# SingleModeScenarioArcPotentialRaceEffectName = 318
# SingleModeScenarioArcSelectionMatchRewardName = 322
# TransferRotationDetailTitle = 319
# TransferRotationDetailComment = 320
# TransferRotationDetailCondition = 321
# StoryEventStoryline = 325
# SkillUpgradeScenario = 326
# GroupSelectGachaName = 327


MDB_CAT_NAMES_LOADED = False
def get_mdb_cat_names():
    global MDB_CAT_NAMES_LOADED
    global MDB_CAT_NAMES

    if not MDB_CAT_NAMES_LOADED:
        MDB_CAT_NAMES_LOADED = True
        chara_json = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "170.json")
        if not os.path.exists(chara_json):
            raise FileNotFoundError(f"Json not found: {chara_json}")
        
        MDB_CAT_NAMES["character_system_text"] = {}

        chara_data = util.load_json(chara_json)
        for chara in chara_data:
            chara_id = str(json.loads(chara['keys'])[0][-1])
            chara_name = chara.get("text", "")
            MDB_CAT_NAMES["character_system_text"][chara_id] = chara_name

    return MDB_CAT_NAMES

class ExpandingTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document().contentsChanged.connect(self.size_change)

        self.height_min = 23
        self.height_max = 65000
    
    def size_change(self):
        doc_height = math.ceil(self.document().size().height()) + 2
        doc_height += 17  # TODO: Scrollbar

        if self.height_min <= doc_height <= self.height_max:
            self.setMinimumHeight(doc_height)
            self.setMaximumHeight(doc_height)
    
    def line_spacing(self, spacing):
        text_cursor = self.textCursor()

        text_block_format = QTextBlockFormat()
        text_cursor.clearSelection()
        text_cursor.select(QTextCursor.Document)
        text_block_format.setLineHeight(spacing, QTextBlockFormat.LineDistanceHeight)
        text_cursor.mergeBlockFormat(text_block_format)

    def insertFromMimeData(self, source: QMimeData) -> None:
        self.insertPlainText(source.text())


UMA_FONT_FAMILY = None
def uma_font(font_size=8, weight=QFont.Weight.Normal, italic=False):
    global UMA_FONT_FAMILY
    if not UMA_FONT_FAMILY:
        font_path = os.path.join(util.MDB_FOLDER_EDITING, "font", "dynamic01.otf")

        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font not found: {font_path}")
        
        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id == -1:
            raise RuntimeError(f"Failed to load font: {font_path}")
        
        UMA_FONT_FAMILY = QFontDatabase.applicationFontFamilies(font_id)[0]

    font = QFont(UMA_FONT_FAMILY, font_size, weight, italic)
    font.setStyleStrategy(QFont.PreferAntialias)
    # font.setHintingPreference(QFont.PreferNoHinting)

    return font