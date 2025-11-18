from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

from datetime import date
from pydantic import BaseModel
from typing import Dict, Any
from typing import List


class GetV1ProjectsIdl3wyngrx9dyxjxramerlxgehkfubnweSettingsResponse200(BaseModel):
    _lastModified: date
    integrations: Dict[str, Any]
    plan: Dict[str, Any]
    edgeFunction: Dict[str, Any]
    analyticsNextEnabled: bool
    middlewareSettings: Dict[str, Any]
    enabledMiddleware: Dict[str, Any]
    metrics: Dict[str, Any]
    legacyVideoPluginsEnabled: bool
    remotePlugins: List[str]
    autoInstrumentationSettings: Dict[str, Any]

from datetime import date
from pydantic import BaseModel
from typing import Dict, Any
from typing import Optional
from uuid import UUID


class PostV1IRequest(BaseModel):
    timestamp: date
    integrations: Dict[str, Any]
    type: str
    userId: Optional[str]
    traits: Dict[str, Any]
    context: Dict[str, Any]
    messageId: str
    anonymousId: UUID
    writeKey: str
    sentAt: date
    _metadata: Dict[str, Any]

from pydantic import BaseModel


class PostV1IResponse200(BaseModel):
    success: bool

from pydantic import BaseModel
from typing import Dict, Any
from typing import List


class PostWebLoginOptionsResponse200(BaseModel):
    option: str
    supported_flows: List[Dict[str, Any]]
    is_onetrust_functional_cookie_denied: bool
    should_show_reset_password_button: bool
    show_system_use_notification: bool
    hide_password_visibility_switch: bool

from pydantic import BaseModel


class PostWebLoginResponse200(BaseModel):
    redirect_url: str

from pydantic import BaseModel
from typing import Dict, Any
from typing import List
from uuid import UUID


class PostRequestV1ConsentreceiptsAnonymousRequest(BaseModel):
    requestInformation: str
    identifier: UUID
    identifierType: str
    customPayload: Dict[str, Any]
    isAnonymous: bool
    test: bool
    purposes: List[Dict[str, Any]]
    dsDataElements: Dict[str, Any]
    source: Dict[str, Any]
    geolocation: Dict[str, Any]

from pydantic import BaseModel
from typing import Dict, Any


class GetAppAsanaStartSessionResponse200(BaseModel):
    session_id: int
    app_data: Dict[str, Any]
    luna_app_data: Dict[str, Any]

from pydantic import BaseModel
from typing import Dict, Any
from typing import List


class GetAppAsanaExperimentsResponse200(BaseModel):
    experiments_data: Dict[str, Any]
    flags: Dict[str, Any]
    enabled_features: List[str]

from pydantic import BaseModel
from typing import List


class GetLlmGetKnowledgeBaseFilterIdResponse200(BaseModel):
    downsampled_knowledge_base_filter: List[str]

from pydantic import BaseModel


class GetHasSingleSessionAndDomainResponse200(BaseModel):
    hasSingleSessionAndDomain: bool
    numSessions: int

from pydantic import BaseModel


class PostAppAsanaReportExecutionContextActivityRequest(BaseModel):
    context_identifier: str

from pydantic import BaseModel
from typing import Dict, Any


class GetGetGlobalCustomFieldSuggestionsFromEphemeralDatastoreResponse200(BaseModel):
    suggestionsFromEds: Dict[str, Any]

